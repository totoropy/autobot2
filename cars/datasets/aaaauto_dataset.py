import numpy as np
import os
from os import listdir
from os.path import isfile, join, isdir

import xml.etree.ElementTree as ET

from chainercv.chainer_experimental.datasets.sliceable import GetterDataset
from chainercv.datasets.voc import voc_utils
from chainercv.utils import read_image


class SliceableLabeledImageDataset(GetterDataset):

    def __init__(self, root='.'):
        super(SliceableLabeledImageDataset, self).__init__()

        # with open(pairs) as f:
        #     self._pairs = [l.split() for l in f]

        self._root = root
        root_len = len(root)

        self.images = []
        for f in sorted(listdir(root)):
            if 'Abarth' in f:
                sub_path = join(root, f)
                if isdir(sub_path):

                    for name in os.listdir(sub_path):
                        sub_sub_path = join(sub_path, name)
                        if os.path.isdir(sub_sub_path):

                            for fn in os.listdir(sub_sub_path):
                                file_path = join(sub_sub_path, fn)
                                if os.path.isfile(file_path):
                                    print(file_path[root_len+1:])
                                    self.images.append((file_path[root_len+1:], 0))

        self.add_getter('img', self.get_image)
        self.add_getter('label', self.get_label)

    def __len__(self):
        return len(self.images)

    def get_image(self, i):
        path, _ = self.images[i]
        return read_image(os.path.join(self._root, path))

    def get_label(self, i):
        # _, label = self._pairs[i]
        return 0 # np.int32(label)


class AAAAutoDataset(GetterDataset):

    """Bounding box dataset for PASCAL `VOC`_.
    .. _`VOC`: http://host.robots.ox.ac.uk/pascal/VOC/voc2012/
    Args:
        data_dir (string): Path to the root of the training data. If this is
            :obj:`auto`, this class will automatically download data for you
            under :obj:`$CHAINER_DATASET_ROOT/pfnet/chainercv/voc`.
        split ({'train', 'val', 'trainval', 'test'}): Select a split of the
            dataset. :obj:`test` split is only available for
            2007 dataset.
        year ({'2007', '2012'}): Use a dataset prepared for a challenge
            held in :obj:`year`.
        use_difficult (bool): If :obj:`True`, use images that are labeled as
            difficult in the original annotation.
        return_difficult (bool): If :obj:`True`, this dataset returns
            a boolean array
            that indicates whether bounding boxes are labeled as difficult
            or not. The default value is :obj:`False`.
    This dataset returns the following data.
    .. csv-table::
        :header: name, shape, dtype, format
        :obj:`img`, ":math:`(3, H, W)`", :obj:`float32`, \
        "RGB, :math:`[0, 255]`"
        :obj:`bbox` [#voc_bbox_1]_, ":math:`(R, 4)`", :obj:`float32`, \
        ":math:`(y_{min}, x_{min}, y_{max}, x_{max})`"
        :obj:`label` [#voc_bbox_1]_, ":math:`(R,)`", :obj:`int32`, \
        ":math:`[0, \#fg\_class - 1]`"
        :obj:`difficult` (optional [#voc_bbox_2]_), ":math:`(R,)`", \
        :obj:`bool`, --
    .. [#voc_bbox_1] If :obj:`use_difficult = True`, \
        :obj:`bbox` and :obj:`label` contain difficult instances.
    .. [#voc_bbox_2] :obj:`difficult` is available \
        if :obj:`return_difficult = True`.
    """

    def __init__(self, data_dir='auto', split='train', year='2012'):
        super(AAAAutoDataset, self).__init__()

        parent_path = os.path.abspath('..')
        image_root = "{}/images".format(parent_path)

        if data_dir == 'auto' and year in ['2007', '2012']:
            data_dir = voc_utils.get_voc(year, split)

        # if split not in ['train', 'trainval', 'val']:

        id_list_file = os.path.join(
            data_dir, 'ImageSets/Main/{0}.txt'.format(split))

        self.ids = [id_.strip() for id_ in open(id_list_file)]

        self.data_dir = data_dir

        self.add_getter('img', self._get_image)
        self.add_getter('label', self._get_label)
        self.keys = ('img', 'label')

    def __len__(self):
        return len(self.ids)

    def _get_image(self, i):
        id_ = self.ids[i]
        img_path = os.path.join(self.data_dir, 'JPEGImages', id_ + '.jpg')
        img = read_image(img_path, color=True)
        return img

    def _get_label(self, i):
        id_ = self.ids[i]
        img_path = os.path.join(self.data_dir, 'JPEGImages', id_ + '.jpg')
        img = read_image(img_path, color=True)
        return "labelAAA"

    def _get_annotations(self, i):
        id_ = self.ids[i]
        anno = ET.parse(
            os.path.join(self.data_dir, 'Annotations', id_ + '.xml'))
        bbox = []
        label = []
        difficult = []
        for obj in anno.findall('object'):
            # when in not using difficult split, and the object is
            # difficult, skipt it.
            if not self.use_difficult and int(obj.find('difficult').text) == 1:
                continue

            difficult.append(int(obj.find('difficult').text))
            bndbox_anno = obj.find('bndbox')
            # subtract 1 to make pixel indexes 0-based
            bbox.append([
                int(bndbox_anno.find(tag).text) - 1
                for tag in ('ymin', 'xmin', 'ymax', 'xmax')])
            name = obj.find('name').text.lower().strip()
            label.append(voc_utils.voc_bbox_label_names.index(name))
        bbox = np.stack(bbox).astype(np.float32)
        label = np.stack(label).astype(np.int32)
        # When `use_difficult==False`, all elements in `difficult` are False.
        difficult = np.array(difficult, dtype=np.bool)
        return bbox, label, difficult
