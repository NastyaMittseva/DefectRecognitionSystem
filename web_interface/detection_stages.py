from weld_segmentator import WeldSegmentator
from weld_classificator import WeldClassificator
from defect_detector import DefectDetector
from intermediate_processor import IntermediateProcessor
from postprocessor import Postprocessor
from defect_classificator import DefectClassificator
import time

weld_segmentator = WeldSegmentator()
medium_processor = IntermediateProcessor()
weld_classificator = WeldClassificator()
defect_detector = DefectDetector()


def weld_segmentation_stage(img_path, save_path):
    start = time.time()  
    weld_segmentator.get_images(img_path)
    weld_segmentator.predict_weld_mask()
    weld_segmentator.apply_threshold()
    result = weld_segmentator.determine_result()
    weld_segmentator.join_mask_img(save_path)
    end = time.time()
    operation_time = round(end - start,4)
    return result, operation_time


def defect_segmentation_stage(img_path, weld_path, path_scale_weld, path_defect_mask, path_results_detection):
    start = time.time()
    weld_segmentator.get_images(img_path)
    weld_segmentator.predict_weld_mask()
    weld_segmentator.apply_threshold()
    weld_segmentator.save_weld_result(weld_path)

    weld_flag = medium_processor.find_weld_boundaries(weld_path)
    print(weld_flag)
    if weld_flag == -1:
        return -1
    medium_processor.add_allowances()
    medium_processor.get_weld_and_gray_bgr(img_path)
    initial_boundar1, initial_boundar2 = medium_processor.form_weld_area(path_scale_weld)

    weld_classificator.get_weld_area(path_scale_weld)
    weld_classificator.predict_weld_class()
    label = weld_classificator.set_label()
    
    if label == "defects are found":
        defect_detector.prepare_input(path_scale_weld)
        defect_detector.predict_defect_mask()
        defect_detector.apply_threshold()
        defect_detector.save_defect_mask(path_defect_mask)

        postprocessor = Postprocessor()
        postprocessor.scale_mask(initial_boundar1, initial_boundar2, path_defect_mask)
        postprocessor.overlay_binary_mask_on_image(img_path, path_results_detection)
    end = time.time()
    operation_time = round(end - start, 4)
    return label, operation_time


def defect_classification_stage(img_path, weld_path, path_scale_weld, path_defect_mask, path_detection_results,
                                path_classification_results):
    start = time.time()
    weld_segmentator.get_images(img_path)
    weld_segmentator.predict_weld_mask()
    weld_segmentator.apply_threshold()
    weld_segmentator.save_weld_result(weld_path)

    weld_flag = medium_processor.find_weld_boundaries(weld_path)
    if weld_flag == -1:
        return -1
    medium_processor.add_allowances()
    medium_processor.get_weld_and_gray_bgr(img_path)
    initial_boundar1, initial_boundar2 = medium_processor.form_weld_area(path_scale_weld)

    weld_classificator.get_weld_area(path_scale_weld)
    weld_classificator.predict_weld_class()
    label = weld_classificator.set_label()

    if label == "defects are found":
        defect_detector.prepare_input(path_scale_weld)
        defect_detector.predict_defect_mask()
        defect_detector.apply_threshold()
        defect_detector.save_defect_mask(path_defect_mask)

        defect_classificator = DefectClassificator()
        exist_defects = defect_classificator.check_mask_on_defects(path_defect_mask)
        if exist_defects:
            defect_classificator.predict_classes_defects(path_scale_weld, path_defect_mask)

        postprocessor = Postprocessor()
        if exist_defects:
            postprocessor.paint_bb_and_classes(img_path, path_classification_results,
                                               defect_classificator.results, initial_boundar1, initial_boundar2)
            label = "defects are classified"
        else:
            label = "defects aren't classified"
            postprocessor.scale_mask(initial_boundar1, initial_boundar2, path_defect_mask)
            postprocessor.overlay_binary_mask_on_image(img_path, path_detection_results)

    end = time.time()
    operation_time = round(end - start, 4)
    return label, operation_time