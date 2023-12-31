#one of the two classes (ArcFace) and one function are used by tps2020.py
import os
import cv2 #opencv (Open Source Computer Vision); pip install opencv-python; https://docs.opencv.org/4.x/d1/dfb/intro.html
#for difference between opencv-contrib-python and opencv-python, see this link:
#https://stackoverflow.com/questions/64902852/the-difference-between-opencv-python-and-opencv-contrib-python
#To test whether cv2 module is available:
#python -c "import cv2"
#python -c "import cv2; print(cv2.__version__)" #4.5.5
import numpy as np
from argparse import ArgumentParser
from utils import walk, progress_bar
from face_models.face_model import ArcFaceModel, FaceNetModel


np.random.seed(42)


class FaceNet:
    def __init__(self, gpu=-1):
        self.__model = FaceNetModel(gpu) #FaceNetModel is a class

    def preprocess(self, image):
        return self.__model.get_input(image)

    def extract(self, image, align=True):
        if align:
            image = self.preprocess(image) #preprocessing should output an image of size (160,160,3)? inconsistent with (112,112,3)?

        if image.shape != (160, 160, 3):
            image = cv2.resize(image, (160, 160))
#extract return a vector of 512 float values
        return self.__model.get_feature(image)


class ArcFace:
    def __init__(self, gpu=-1):
        self.__model = ArcFaceModel(gpu) #ArcFaceModel is a class

    def preprocess(self, image): #image is of class 'numpy.ndarray'; returns a numpy.ndarray
        return self.__model.get_input(image)

    def extract(self, image, align=True):
        if align:
            image = self.preprocess(image) #preprocessing should output an image of size (112,112,3)

        if image.shape != (3, 112, 112): #should be (112, 112, 3)?
            image = cv2.resize(image, (112, 112))
            image = np.rollaxis(cv2.cvtColor(image, cv2.COLOR_RGB2BGR), 2, 0)
#extract return a vector of 512 float values
        return self.__model.get_feature(image)

#return a 2D array of the shape:
#number of rows is the image count;
#number of columns is 513 (last column is 1-based subject_id)
#this function will display a progress bar
def extract_dataset(dataset, extractor="arcface", gpu=-1):
    if extractor == "arcface":
        face = ArcFace(gpu)
    else:
        face = FaceNet(gpu)

    dataset_path = os.path.join(os.path.abspath(""), "images", dataset) #dataset will be "lfw" or "gtdb"

    file_cnt = len(walk(dataset_path))
    features = np.zeros((file_cnt, 513))
    #features_flip = np.zeros((file_cnt, 513)) #omitted by Kai

    image_cnt = 0
    subjects = os.listdir(dataset_path)
    subjects = [x for _, x in sorted(
        zip([subject.lower() for subject in subjects], subjects))] # this is to do case-insensitive sorting
    for subject_id, subject in enumerate(subjects):
        progress_bar(dataset + " " + extractor, float(image_cnt + 1) / file_cnt)

        for image in os.listdir(os.path.join(dataset_path, subject)):
            image = cv2.imread(os.path.join(dataset_path, subject, image))

            feature = face.extract(image) #the return value of extract here should be a row vector of 512 elements
            features[image_cnt, :] = np.append(feature, subject_id + 1) #the return value of append here should be a row vector of 513 elements

            #feature_flip = face.extract(cv2.flip(image, 1)) #omitted by Kai
            #features_flip[image_cnt, :] = np.append(feature_flip, subject_id + 1) #omitted by Kai

            image_cnt += 1

    #return features, features_flip #omitted by Kai
    return features


if __name__ == "__main__":
    '''
    facenet = FaceNet()

    img_1 = cv2.imread(os.path.join(
        os.path.abspath(""), "src", "face_models", "tom1.jpg"))
    img_2 = cv2.imread(os.path.join(
        os.path.abspath(""), "src", "face_models", "adrien.jpg"))

    feat_1 = facenet.extract(img_1)
    feat_2 = facenet.extract(img_2)
    print(np.sum(np.square(feat_1 - feat_2)))
    print(np.dot(feat_1, feat_2.T))

    cv2.imshow("before", img_1)
    img = facenet.preprocess(img_1)
    cv2.imshow("after", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    arcface = ArcFace()

    feat_1 = arcface.extract(img_1)
    feat_2 = arcface.extract(img_2)
    print(np.sum(np.square(feat_1 - feat_2)))
    print(np.dot(feat_1, feat_2.T))

    cv2.imshow("before", img_2)
    img = arcface.preprocess(img_2)
    cv2.imshow("after", cv2.cvtColor(
        np.rollaxis(img, 0, 3), cv2.COLOR_RGB2BGR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    '''
    parser = ArgumentParser()
    parser.add_argument("-d", "--dataset", required=True, help="dataset to use in feature extraction")
    parser.add_argument("-m", "--method", required=True, choices=["arcface", "facenet"], help="method to use in feature extraction")
    parser.add_argument("-gpu", "--gpu", required=False, type=int, default=-1, help="gpu to use in feature extraction")
    args = vars(parser.parse_args())
#extract_dataset is a function in this module
    #features, features_flip = extract_dataset(args["dataset"], args["method"], args["gpu"])
    features = extract_dataset(args["dataset"], args["method"], args["gpu"])
#are these used to create files like lfw_arcface_feat.npz and lfw_facenet_feat.npz in downloaeded features.tar.gz?
    np.savez_compressed(os.path.join(os.path.abspath(""), "data", "{}_{}_feat.npz".format(args["dataset"], args["method"])), features)
    #np.savez_compressed(os.path.join(os.path.abspath(""), "data", "{}_{}_feat_flip.npz".format(args["dataset"], args["method"])), features_flip)
