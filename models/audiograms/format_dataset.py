#!/usr/bin/env python3
"""
Copyright (c) 2020 Carleton University Biomedical Informatics Collaboratory

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""
from typing import List
from types import SimpleNamespace
import argparse, os, json, shutil
from tqdm import tqdm
import os.path as path
import numpy as np
from PIL import Image

def extract_audiograms(annotation: dict, image: Image) -> List[tuple]:
    """Extracts the bounding boxes of audiograms into a tuple compatible
    the YOLOv5 format.

    Parameters
    ----------
    annotation : dict
    A dictionary containing the annotations for the audiograms in a report.

    image : Image
    The image in PIL format corresponding to the annotation.

    Returns
    -------
    tuple
    A tuple of the form
    (class index, x_center, y_center, width, height) where all coordinates
    and dimensions are normalized to the width/height of the image.
    """
    audiogram_label_tuples = []
    image_width, image_height = image.size
    for audiogram in annotation:
        bounding_box = audiogram["boundingBox"]
        x_center = (bounding_box["x"] + bounding_box["width"] / 2) / image_width
        y_center = (bounding_box["y"] + bounding_box["height"] / 2) / image_height
        box_width = bounding_box["width"] / image_width
        box_height = bounding_box["height"] / image_width
        audiogram_label_tuples.append((0, x_center, y_center, box_width, box_height))
    return audiogram_label_tuples

def create_yolov5_file(bboxes: List[tuple], filename: str):
    # Turn the bounding boxes into a string with a bounding box
    # on each line
    file_content = "\n".join([
        f"{bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]} {bbox[4]}"
        for bbox in bboxes
    ])

    # Save to a file
    with open(filename, "w") as output_file:
        output_file.write(file_content)

def create_directory_structure(data_dir: str):
    try:
        shutil.rmtree(path.join(data_dir))
    except:
        pass
    os.mkdir(path.join(data_dir))
    os.mkdir(path.join(data_dir, "images"))
    os.mkdir(path.join(data_dir, "images", "train"))
    os.mkdir(path.join(data_dir, "images", "validation"))
    os.mkdir(path.join(data_dir, "labels"))
    os.mkdir(path.join(data_dir, "labels", "train"))
    os.mkdir(path.join(data_dir, "labels", "validation"))

def all_labels_valid(labels: List[tuple]):
    for label in labels:
        for value in label[1:]:
            if value < 0 or value > 1:
                return False
    return True

def main(args: SimpleNamespace):
    # Find all the JSON files in the input directory
    report_ids = [
        filename.rstrip(".json")
        for filename in os.listdir(path.join(args.annotations_dir))
        if filename.endswith(".json")
        and path.exists(path.join(args.images_dir, filename.rstrip(".json") + ".jpg"))
    ]

    # Shuffle
    np.random.seed(seed=42) # for reproducibility of the shuffle
    np.random.shuffle(report_ids)

    # Create the directory structure in which the images and annotations
    # are to be stored
    create_directory_structure(args.data_dir)

    # Iterate through the report ids, extract the annotations in YOLOv5 format
    # and place the file in the correct directory, and the image in the correct
    # directory.
    for i, report_id in enumerate(tqdm(report_ids)):
        # Decide if the image is going into the training set or validation set
        directory = (
            "train" if i < args.train_frac * len(report_ids) else "validation"
        )

        # Load the annotation`
        annotation_content = open(
            path.join(args.annotations_dir, f"{report_id}.json")
        )
        annotation = json.load(annotation_content)

        # Open the corresponding image to get its dimensions
        image = Image.open(os.path.join(args.images_dir, f"{report_id}.jpg"))
        width, height = image.size

        # Audiogram labels
        audiogram_labels = extract_audiograms(annotation, image)

        if not all_labels_valid(audiogram_labels):
            continue

        create_yolov5_file(
            audiogram_labels,
            path.join(args.data_dir, "labels", directory, f"{report_id}.txt")
        )
        image.save(
            path.join(args.data_dir, "images", directory, f"{report_id}.jpg")
        )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=(
        "Script that formats the training set for transfer learning via "
        "the YOLOv5 model."
    ))
    parser.add_argument("-d", "--data_dir", type=str, required=True, help=(
        "Path to the directory containing the data. It should have 3 "
        "subfolders named `images`, `annotations` and `labels`."
    ))
    parser.add_argument("-a", "--annotations_dir", type=str, required=True, help=(
        "Path to the directory containing the annotations in the JSON format." 
    ))
    parser.add_argument("-i", "--images_dir", type=str, required=True, help=(
        "Path to the directory containing the images." 
    ))
    parser.add_argument("-f", "--train_frac", type=float, required=True, help=(
        "Fraction of images to be used for training. (e.g. 0.8)"
    ))
    args = parser.parse_args()

    main(args)

