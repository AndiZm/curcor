import logging

class log:
    path=None
    last_cam_x=None
    last_cam_z=None
    last_mir_z=None
    last_az=None
    last_alt=None
    last_time=None
    
    def __init__(self, path="../../../LOG"):
        self.path=path
        logging.basicConfig(filename="{0}/log.log".format(path), level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d-%H:%M:%S')
    def log(self, message):
        print(message)
        logging.debug(message)
    def set_experimental(self, last_cam_x, last_cam_z, last_mir_z, last_az, last_alt, last_time):
        self.last_cam_x=last_cam_x
        self.last_cam_z=last_cam_z
        self.last_mir_z=last_mir_z
        self.last_alt=last_alt
        self.last_az=last_az
        self.last_time=last_time
    def get_last(self):
        return self.last_cam_x, self.last_cam_z, self.last_mir_z, self.last_az, self.last_alt, self.last_time
