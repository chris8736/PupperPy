import random
from ControllerState import ControllerState
from CameraData import BoundingBox
from CameraData import CameraData

TURNING_VELOCITY = .1
FORWARD_VELOCITY = .1
BOX_SIZE_LIMIT = 200
cam_dat = CameraData()
pos = None

"""
Returns a new robot command based off camera and position data.
"""


def moveToTarget(cam_data, pos_data):
    new_command = ControllerState()
    if cam_dat.target_bounding_box.area() > BOX_SIZE_LIMIT:  # if too close to object, stop
        return new_command

    # calculate how far bounding box is from center
    target_x = cam_dat.target_bounding_box.median_point()[0]
    offset = target_x - cam_dat.SIZE_X / 2

    new_command.left_analog_y = FORWARD_VELOCITY
    # adjust yaw based on offset
    new_command.right_analog_x = offset * TURNING_VELOCITY / cam_dat.SIZE_X

    print(new_command.right_analog_x)

    return new_command


while True:
    robot_command = ControllerState()
    if cam_dat:
        cam_dat.target_bounding_box = BoundingBox(920, random.uniform(
            0, 540), random.uniform(0, 160), random.uniform(0, 540))
        robot_command = moveToTarget(cam_dat, pos)
    else:
        pass
    # print(robot_command)
