# Pixano Cookbook

Recipes to prepare and import sample datasets into Pixano.

Assume you already ran `uv run pixano init ./data` in your Pixano project (creates `./data` for library, media, models). All `pixano data import` examples below use `./data` as the Pixano data directory; adjust paths to your `info.py` if your layout differs.

---

## Summary: where the data comes from

**You download or obtain the data yourself**

- **[nuScenes — LIDAR_TOP](#nuscenes-lidar_top-point-clouds)** — Get archives from the [nuScenes download page](https://www.nuscenes.org/download) (account and license terms). After unpacking, import the `samples/LIDAR_TOP` folder.
- **[DAVIS 2017](#davis-2017-video-segmentation)** — Download the official DAVIS dataset and unpack it; point the generator at that root.
- **[FLIR ADAS v2](#flir-adas-v2-rgb--thermal)** — Register on [FLIR Conservator](https://adas-dataset-v2.flirconservator.com/) and download the release; the script expects a full local tree (see the FLIR section).
- **[MEL](#mel-image--text-entity-linking)** — There is no sample generator here; prepare your own folder (e.g. `mel_source`) to match your pipeline and `mel/info.py`.

**Scripts fetch the dataset for you**

- **[Pascal VOC 2007](#pascal-voc-2007-images)** — `voc/generate_sample.py` downloads VOC 2007 zips into a cache and builds a sample folder.
- **[VQAv2](#vqav2)** — `vqav2/generate_sample.py` pulls `merve/vqav2-small` from Hugging Face when you run it.

**You supply the media; the script only reshapes it**

- **[Unlabeled images](#unlabeled-images)** — Any folder of images you choose.
- **[Unlabeled videos](#unlabeled-videos)** — Any folder of videos you choose.

---

## nuScenes `LIDAR_TOP` (point clouds)

### Where to get the data

- Official downloads: [https://www.nuscenes.org/download](https://www.nuscenes.org/download)

Create an account, accept the terms, then download the splits you need. For a small trial, use the **mini** split (`v1.0-mini`).

### How to download

1. Sign in on the nuScenes site and open the download section.
2. Download the archives for your chosen split (e.g. **mini**: map expansion + mini metadata + mini sensor blobs — follow the site’s file list for `v1.0-mini`).
3. Extract everything into one parent folder (often named `nuscenes` or similar) so that you obtain the folder layout below.

### Expected layout (after extraction)

Point clouds for the vehicle’s main LiDAR live under `samples/LIDAR_TOP/`. A typical mini layout looks like:

```text
<your_nuscenes_root>/
  maps/
  samples/
    LIDAR_TOP/          ← import this folder (or a copy): one file per keyframe, e.g. *.pcd.bin
    CAM_FRONT/
    ...
  sweeps/
  v1.0-mini/            ← JSON tables (version metadata)
```

The cookbook import targets **only** the directory that contains the LiDAR sample files (e.g. `samples/LIDAR_TOP`), not the whole nuScenes tree.

### Import into Pixano

From your Pixano project directory (with `./data` initialized), run:

```bash
uv run pixano data import ./data /path/to/v1.0-mini/samples/LIDAR_TOP \
  --info /path/to/pixano-cookbook/data_importation/nuscenes_lidar_top/info.py:dataset_info \
  --mode overwrite
```

Replace `/path/to/v1.0-mini/samples/LIDAR_TOP` with the actual path to your extracted `LIDAR_TOP` folder, and point `--info` at this repo’s `nuscenes_lidar_top/info.py` if it is not next to your project.

---

## Pascal VOC 2007 (images)

**Install / prepare:** no manual dataset download. The script downloads VOC 2007 into a cache under `~/.cache/pixano/voc2007/` and builds a small export.

**Requirements:** `pillow` (see script docstring).

**Generate a sample** (from the Pixano repo or with paths adjusted):

```bash
uv run python /path/to/pixano-cookbook/data_importation/voc/generate_sample.py ./voc_sample --num-samples 30
```

**Import:**

```bash
uv run pixano data import ./data ./voc_sample \
  --info /path/to/pixano-cookbook/data_importation/voc/info.py:dataset_info
```

---

## VQAv2

**Install / prepare:** loads `merve/vqav2-small` from Hugging Face when you run the generator.

**Requirements:** `datasets`, `pillow`.

**Generate:**

```bash
uv run python /path/to/pixano-cookbook/data_importation/vqav2/generate_sample.py ./vqav2_sample --num-samples 50
```

**Import:**

```bash
uv run pixano data import ./data ./vqav2_sample \
  --info /path/to/pixano-cookbook/data_importation/vqav2/info.py:dataset_info
```

---

## DAVIS 2017 (video segmentation)

**Install / prepare:** download the DAVIS 2017 dataset from the official source and unpack it so you have `JPEGImages/`, `Annotations/`, and `ImageSets/` at the dataset root.

**Generate** (point `davis_root` at that root):

```bash
uv run python /path/to/pixano-cookbook/data_importation/davis/generate_sample.py ./davis_sample /path/to/DAVIS --num-samples 5
```

**Import:**

```bash
uv run pixano data import ./data ./davis_sample \
  --info /path/to/pixano-cookbook/data_importation/davis/info.py:dataset_info
```

---

## FLIR ADAS v2 (RGB + thermal)

**Install / prepare:** manual download from [FLIR ADAS dataset](https://adas-dataset-v2.flirconservator.com/). You need a layout that includes `rgb_to_thermal_vid_map.json` and the `video_rgb_test/` / `video_thermal_test/` trees (see `data_importation/flir/generate_sample.py` for the exact layout).

**Generate:**

```bash
uv run python /path/to/pixano-cookbook/data_importation/flir/generate_sample.py ./flir_sample /path/to/flir_adas_v2 --num-samples 50
```

For sequence mode with `video_dataset_info`:

```bash
uv run python /path/to/pixano-cookbook/data_importation/flir/generate_sample.py ./flir_sample /path/to/flir_adas_v2 --mode video --num-samples 10
```

**Import (static frame pairs):**

```bash
uv run pixano data import ./data ./flir_sample \
  --info /path/to/pixano-cookbook/data_importation/flir/info.py:dataset_info
```

**Import (video / sequence workspace):**

```bash
uv run pixano data import ./data ./flir_sample \
  --info /path/to/pixano-cookbook/data_importation/flir/info.py:video_dataset_info
```

---

## Unlabeled images

**Install / prepare:** put images in a folder (e.g. `.jpg`, `.png`).

**Generate:**

```bash
uv run python /path/to/pixano-cookbook/data_importation/unlabeled_images_folder/generate_sample.py \
  --input_folder ./images --output ./sample_images
```

**Import:**

```bash
uv run pixano data import ./data ./sample_images \
  --info /path/to/pixano-cookbook/data_importation/unlabeled_images_folder/info.py:dataset_info
```

---

## Unlabeled videos

**Install / prepare:** place video files (e.g. `.mp4`, `.mov`) in a folder.

**Generate:**

```bash
uv run python /path/to/pixano-cookbook/data_importation/unlabeled_videos_folder/generate_sample.py \
  --input_folder ./videos --output ./sample_videos
```

**Import:**

```bash
uv run pixano data import ./data ./sample_videos \
  --info /path/to/pixano-cookbook/data_importation/unlabeled_videos_folder/info.py:dataset_info
```

---

## MEL (image–text entity linking)

**Install / prepare:** there is no `generate_sample.py` in this cookbook; you must build a directory (e.g. `./mel_source`) that matches your annotation pipeline and the expectations of `data_importation/mel/info.py`.

**Import:**

```bash
uv run pixano data import ./data ./mel_source \
  --info /path/to/pixano-cookbook/data_importation/mel/info.py:dataset_info
```
