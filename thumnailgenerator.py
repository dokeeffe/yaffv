#!/usr/bin/env python
import glob
from pathlib import Path
import numpy as np
import os
from astropy.io import fits
from PIL import Image
from multiprocessing import Pool


class ThumbGenerator:

    def _save_tmp_jpg_from_fits(self, file, thumbnail):
        with fits.open(file) as hdul:
            data = hdul[0].data
            if data is None:
                data = hdul[1].data

            clean = data[np.isfinite(data)]
            mean = clean.mean()
            std = clean.std()
            vmin = mean - std
            vmax = mean + std * 3

            data[data > vmax] = vmax
            data[data < vmin] = vmin
            data = (data - vmin) / (vmax - vmin)
            data = (255 * data).astype(np.uint8)
            image = Image.fromarray(data, 'L')
            print('saving {}'.format(thumbnail))
            image.save(thumbnail)


    def generate_thumb(self, file):
        fits_path = Path(file)
        hidden_thumbnail_dir = os.path.join(fits_path.parent, '.thumbnails')
        if not os.path.exists(hidden_thumbnail_dir):
            os.mkdir(hidden_thumbnail_dir)
        thumbnail = os.path.join(hidden_thumbnail_dir, os.path.basename(fits_path.stem + '.jpg'))
        if not os.path.exists(thumbnail):
            with fits.open(file) as hdul:
                data = hdul[0].data
            if data is None:
                data = hdul[1].data

            clean = data[np.isfinite(data)]
            mean = clean.mean()
            std = clean.std()
            vmin = mean - std
            vmax = mean + std * 3

            data[data > vmax] = vmax
            data[data < vmin] = vmin
            data = (data - vmin) / (vmax - vmin)
            data = (255 * data).astype(np.uint8)
            image = Image.fromarray(data, 'L')
            print('saving {}'.format(thumbnail))
            image.save(thumbnail)

    def generate(self, path):
        data_files = glob.glob(path)

        with Pool(4) as p:
            print(p.map(self.generate_thumb, data_files))




if __name__ == '__main__':
    import sys

    app = ThumbGenerator()
    sys.exit(app.generate('/home/dokeeffe/pCloudDrive/ObservatoryPC/CalibratedLight/**/*.fits'))
