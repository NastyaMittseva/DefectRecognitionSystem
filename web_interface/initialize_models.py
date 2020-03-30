from instance_normalization import InstanceNormalization
from my_upsampling_2d_v2 import MyUpSampling2D
from FgSegNet_v2_module import loss, acc, mean_iou, iou_coef, mAP, auc, recall_m, precision_m, f1_m
from efficientnet.layers import Swish, DropConnect
from efficientnet.model import ConvKernalInitializer
from tensorflow.python.keras.utils import get_custom_objects
from tensorflow.python.keras.models import load_model as load_model1
from keras.models import load_model as load_model2
from Unet_module import Unet_module
# import tensorflow as tf
# import keras


def init_models():
    """ Инициализация всех моделей. """
    weld_segmentator_path = './models/weldSegmentation/FgSegNet_v2/v2_mdl_welds_Dataset_v5_16-0.02.h5'
    weld_classificator_path = './models/weldClassification/Efficientnet_b3/efficientnet-b3_binary_welds3_36-0.00-1.00.h5'
    defect_segmentator_path = './models/defectSegmentation/FgSegNet_M/mdl_defects_dataset_v6_only_defects_24-0.05.h5'
    defect_classificator_path = './models/defectClassification/Unet/multi_defect_detection_aug_211_UNet_90-0.01.hdf5'

    global weld_classif_mdl, weld_segment_mdl, defect_segment_mdl
    get_custom_objects().update({
        'ConvKernalInitializer': ConvKernalInitializer,
        'Swish': Swish,
        'DropConnect': DropConnect
    })
    weld_classif_mdl = load_model1(weld_classificator_path)
    # global graph_weld_classif
    # graph_weld_classif = tf.get_default_graph()
    weld_classif_mdl._make_predict_function()


    weld_segment_mdl = load_model2(weld_segmentator_path,
                       custom_objects={'MyUpSampling2D': MyUpSampling2D,'InstanceNormalization': InstanceNormalization,
                                       'loss': loss, 'acc': acc, 'f1_m': f1_m,'mean_iou': mean_iou,'iou_coef': iou_coef,
                                       'mAP': mAP, 'auc': auc, 'recall_m': recall_m, 'precision_m': precision_m})
    weld_segment_mdl._make_predict_function()

    defect_segment_mdl = load_model2(defect_segmentator_path,
                         custom_objects={'MyUpSampling2D': MyUpSampling2D, 'loss': loss, 'acc': acc,'f1_m': f1_m,
                                         'mean_iou': mean_iou, 'iou_coef': iou_coef,'mAP': mAP, 'auc': auc,
                                         'recall_m': recall_m, 'precision_m': precision_m})
    defect_segment_mdl._make_predict_function()

    filters_dims = [64, 128, 256, 512]
    input_shape = (384, 1152, 3)
    unet = Unet_module(input_shape, filters_dims)
    defect_classif_mdl = unet.Unet()
    defect_classif_mdl.load_weights(defect_classificator_path)
    defect_classif_mdl._make_predict_function()

    return weld_segment_mdl, weld_classif_mdl, defect_segment_mdl, defect_classif_mdl
