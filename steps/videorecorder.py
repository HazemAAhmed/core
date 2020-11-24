from datetime import datetime
import os

from subprocess import call

from radish import before, after, world


CMD = 'videorecording'


class SubTitles:

    def __init__(self, name):
        self.name = name
        self.text = None
        self.started = False
        self.startofvideo = False
        self.index = 0

    def start(self, text):
        print("subtitles start {}/{}".format(self.name, text))

        if self.text:
            self._write(
                self.started,
                datetime.now() - self.startofvideo)

        self.text = text
        self.started = datetime.now() - self.startofvideo

    def _write(self, start, stop):
        self.index += 1
        start = _formatdelta(start)
        stop = _formatdelta(stop)

        fn = os.path.join(world.config.user_data['reportsdir'], "{}.srt".format(self.name))
        print("updating srt file {}".format(fn))
        with open(fn, "a") as srtfile:
            srtfile.writelines([
                '\n',
                '{}\n'.format(self.index),
                "{} --> {}\n".format(start, stop),
                '{}\n'.format(self.text)])
            srtfile.close()


class VideoRecorder:

    def __init__(self, name):
        self.started = False
        self.name = name
        self.subtitles = SubTitles(self.name)

    def start(self):
        if self.started:
            return
        print("starting video recording for %s to %s"
              % (self.name, world.config.user_data['reportsdir']))
        call([CMD,
              "start",
              os.environ["DISPLAY"],
              world.config.user_data['reportsdir'],
              # 'reports/',
              "%s-video.mp4" % self.name])
        self.started = datetime.now()
        self.subtitles.startofvideo = self.started

    def stop(self):
        print("stopping video recording for %s" % self.name)
        self.started = False
        call([CMD,
              "stop",
              os.environ["DISPLAY"],
              world.config.user_data['reportsdir'],
              "%s-video.mp4" % self.name])


@before.each_step
def subtitle_step(step):
    world.vr.subtitles.start(step.sentence)


@before.each_feature
def start_videorecording(feature):
    fn = _feature2name(feature)
#   print(feature.line)
#   print(feature.sentence)
#   print(feature.keyword)
#   print(feature.description)
#   print(feature.path)
    print("start video recording for '%s'" % fn)
    world.vr = VideoRecorder(fn)
    world.vr.start()
    world.vr.subtitles.start(_feature2name(feature))


@after.each_feature
def stop_videorecording(feature):
    fn = _feature2name(feature)
    print("*** stop video recording for '%s'" % fn)
    if not world.vr or not world.vr.started:
        return
    world.vr.stop()


def _feature2name(feature):
    return os.path.basename(feature.path)


def _formatdelta(timedelta):
    # return timedelta.strftime("%H:%M:%S,%fff")
    TFT = "%02d:%02d:%02d,%03d"
    return TFT % (
        timedelta.seconds // 3600,
        timedelta.seconds % 3600 // 60,
        timedelta.seconds % 3600 % 60,
        timedelta.microseconds // 1000)
