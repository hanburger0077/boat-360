"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Manually select points to get the projection map
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import argparse
import os
import numpy as np
import cv2
from surround_view import FisheyeCameraModel, PointSelector, display_image
import surround_view.param_settings as settings


def _default_preview_path(camera_name: str) -> str:
    out_dir = os.path.join(os.getcwd(), "outputs", "projections")
    return os.path.join(out_dir, f"{camera_name}_proj.png")

def _default_undistort_path(camera_name: str) -> str:
    out_dir = os.path.join(os.getcwd(), "outputs", "undistorted")
    return os.path.join(out_dir, f"{camera_name}_und.png")


def get_projection_map(camera_model, image, preview_path=None):
    und_image = camera_model.undistort(image)
    name = camera_model.camera_name
    gui = PointSelector(und_image, title=name)
    dst_points = settings.project_keypoints[name]
    choice = gui.loop()
    if choice > 0:
        if len(gui.keypoints) != 4:
            print("Expected 4 points, got {}. Abort.".format(len(gui.keypoints)))
            return False
        src = np.float32(gui.keypoints)
        dst = np.float32(dst_points)
        camera_model.project_matrix = cv2.getPerspectiveTransform(src, dst)
        proj_image = camera_model.project(und_image)

        if preview_path:
            os.makedirs(os.path.dirname(preview_path), exist_ok=True)
            ok = cv2.imwrite(preview_path, proj_image)
            if ok:
                print(f"saved projected image to: {preview_path}")
            else:
                print(f"failed to save projected image to: {preview_path}")

        ret = display_image("Bird's View", proj_image)
        if ret > 0:
            return True
        if ret < 0:
            cv2.destroyAllWindows()

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-camera", required=True,
                        choices=["front", "back", "left", "right"],
                        help="The camera view to be projected")
    parser.add_argument("-scale", nargs="+", default=None,
                        help="scale the undistorted image")
    parser.add_argument("-shift", nargs="+", default=None,
                        help="shift the undistorted image")
    parser.add_argument("--save_preview", action="store_true",
                        help="save projected image to outputs/projections/<camera>_proj.png")
    parser.add_argument("--preview_path", default=None,
                        help="override preview output path (png/jpg)")
    parser.add_argument("--save_undistorted", action="store_true",
                        help="save undistorted image to outputs/undistorted/<camera>_und.png and exit")
    parser.add_argument("--undistorted_path", default=None,
                        help="override undistorted output path (png/jpg)")
    args = parser.parse_args()

    if args.scale is not None:
        scale = [float(x) for x in args.scale]
    else:
        scale = (1.0, 1.0)

    if args.shift is not None:
        shift = [float(x) for x in args.shift]
    else:
        shift = (0, 0)

    camera_name = args.camera
    camera_file = os.path.join(os.getcwd(), "yaml", camera_name + ".yaml")
    images_dir = os.path.join(os.getcwd(), "images")
    candidate_image_files = [
        os.path.join(images_dir, camera_name + ext)
        for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG")
    ]
    image_file = next((p for p in candidate_image_files if os.path.isfile(p)), candidate_image_files[0])
    image = cv2.imread(image_file)
    if image is None:
        print("Failed to read image file: {}".format(image_file))
        return
    print("using image file: {}".format(image_file))
    camera = FisheyeCameraModel(camera_file, camera_name)
    camera.set_scale_and_shift(scale, shift)

    if args.save_undistorted or args.undistorted_path:
        und = camera.undistort(image)
        out_path = args.undistorted_path or _default_undistort_path(camera_name)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        ok = cv2.imwrite(out_path, und)
        if ok:
            print(f"saved undistorted image to: {out_path}")
        else:
            print(f"failed to save undistorted image to: {out_path}")
        return

    preview_path = None
    if args.preview_path:
        preview_path = args.preview_path
    elif args.save_preview:
        preview_path = _default_preview_path(camera_name)

    success = get_projection_map(camera, image, preview_path=preview_path)
    if success:
        print("saving projection matrix to yaml")
        camera.save_data()
    else:
        print("failed to compute the projection map")


if __name__ == "__main__":
    main()
