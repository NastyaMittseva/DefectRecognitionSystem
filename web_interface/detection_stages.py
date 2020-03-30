from weld_segmentator_v2 import WeldSegmentator_FgSegNet_v2
from weld_classificator import WeldClassificator
from defect_detector_M import DefectDetector
from initialize_models import init_models
from intermediate_processor import IntermediateProcessor
from postprocessor import Postprocessor
from defect_classificator import DefectClassificator
import time

weld_segment_mdl, weld_classif_mdl, defect_segment_mdl, defect_classif_mdl = init_models()
weld_segmentator = WeldSegmentator_FgSegNet_v2()
medium_processor = IntermediateProcessor()
weld_classificator = WeldClassificator()
defect_detector = DefectDetector()


def weld_segmentation_stage(img_path, save_path):
    start = time.time()
    weld_segmentator.get_images(img_path)
    weld_segmentator.predict_weld_mask(weld_segment_mdl)
    weld_segmentator.apply_threshold()
    result = weld_segmentator.determine_result()
    weld_segmentator.join_mask_img(save_path)
    end = time.time()
    operation_time = round(end - start,4)
    return result, operation_time


def defect_segmentation_stage(img_path, weld_path, path_scale_weld, path_defect_mask, path_results_detection):
    start = time.time()
    print(img_path)
    weld_segmentator.get_images(img_path)
    weld_segmentator.predict_weld_mask(weld_segment_mdl)
    weld_segmentator.apply_threshold()
    print(weld_path)
    weld_segmentator.save_weld_result(weld_path)

    weld_flag = medium_processor.find_weld_boundaries(weld_path)
    if weld_flag == -1:
        return -1
    medium_processor.add_allowances()
    medium_processor.get_weld_and_gray_bgr(img_path)
    initial_boundar1, initial_boundar2 = medium_processor.form_weld_area(path_scale_weld)

    # weld_classificator.get_weld_area(path_scale_weld)
    # weld_classificator.predict_weld_class(weld_classif_mdl)
    # label = weld_classificator.set_label()

    # if label == "Дефекты найдены":
    label = ""
    defect_detector.prepare_input(path_scale_weld)
    defect_detector.predict_defect_mask(defect_segment_mdl)
    defect_detector.apply_threshold()
    defect_detector.save_defect_mask(path_defect_mask)

    postprocessor = Postprocessor()
    postprocessor.scale_mask(initial_boundar1, initial_boundar2, path_defect_mask)
    postprocessor.overlay_binary_mask_on_image(img_path, path_results_detection)
    end = time.time()
    operation_time = round(end - start, 4)
    return label, operation_time


def defect_classification_stage(img_path, weld_path, path_scale_weld, path_defect_mask, path_results_detection,
                                path_white_bkg, path_mask_by_classes, path_results_by_class):
    start = time.time()
    print(img_path)
    weld_segmentator.get_images(img_path)
    weld_segmentator.predict_weld_mask(weld_segment_mdl)
    weld_segmentator.apply_threshold()
    print(weld_path)
    weld_segmentator.save_weld_result(weld_path)

    weld_flag = medium_processor.find_weld_boundaries(weld_path)
    if weld_flag == -1:
        return -1
    medium_processor.add_allowances()
    medium_processor.get_weld_and_gray_bgr(img_path)
    initial_boundar1, initial_boundar2 = medium_processor.form_weld_area(path_scale_weld)

    # weld_classificator.get_weld_area(path_scale_weld)
    # weld_classificator.predict_weld_class(weld_classif_mdl)
    # label = weld_classificator.set_label()

    # if label == "Дефекты найдены":
    label = ""
    defect_detector.prepare_input(path_scale_weld)
    defect_detector.predict_defect_mask(defect_segment_mdl)
    defect_detector.apply_threshold()
    defect_detector.save_defect_mask(path_defect_mask)


    defect_classificator = DefectClassificator()
    exist_defects = defect_classificator.check_mask_on_defects(path_defect_mask)
    if exist_defects:
        defect_classificator.get_defect_mask(path_scale_weld, path_defect_mask, path_white_bkg)
        defect_classificator.predict_classes_defects(defect_classif_mdl)
        defect_classificator.combine_and_save_mask(path_mask_by_classes)

    postprocessor = Postprocessor()
    if exist_defects:
        postprocessor.scale_mask(initial_boundar1, initial_boundar2, path_mask_by_classes)
        postprocessor.overlay_classes_mask_on_image(img_path, path_results_by_class)
    else:
        postprocessor.scale_mask(initial_boundar1, initial_boundar2, path_defect_mask)
        postprocessor.overlay_binary_mask_on_image(img_path, path_results_detection)

    end = time.time()
    operation_time = round(end - start, 4)
    return label, operation_time