#!/usr/bin/env python
import sys
import os.path

HOME = os.path.expanduser("~/")

#the glx tests:
GLX_SPHERES = ["/usr/bin/glxspheres"]
GLX_GEARS = ["/usr/bin/glxgears", "-geometry", "1240x900"]
NO_SHAPING = (0, 0, 0)

#the plain X11 tests:
X11_PERF = ["/usr/bin/x11perf", "-resize", "-all"]
XTERM_TEST = ["/usr/bin/xterm", "-geometry", "160x60", "-e", "while true; do dmesg; done"]
FAKE_CONSOLE_USER_TEST = ["/usr/bin/xterm", "-geometry", "160x60", "-e", "PYTHONPATH=`pwd` ./tests/xpra/simulate_console_user.py"]

#the screensaver tests:
XSCREENSAVERS_PATH = "/usr/libexec/xscreensaver"

#games
NEXUIZ_TEST = ["/usr/bin/nexuiz-glx", "-benchmark", "demos/demo1", "-nosound"]
XONOTIC_TEST = ["/opt/Xonotic/xonotic-linux64-glx", "-basedir", "/opt/Xonotic", "-benchmark", "demos/the-big-keybench"]

VLC_BIN = "/usr/bin/vlc"
MPLAYER_BIN = "/usr/bin/mplayer"
GTKPERF_TEST = "bash -c 'while true; do gtkperf -a; done'"
MPLAYER_SOUND_LOOP_TEST = "while true; do %s ./test.mp3; done" % MPLAYER_BIN
VLC_SOUND_TEST = (VLC_BIN, "-L", "--audio-visual=visual", "./test.mp3")
VLC_VIDEO_TEST = (VLC_BIN, "-L", "./test.avi")
MPLAYER_VIDEO_TEST = "while true; do %s test.avi; done" % MPLAYER_BIN

class Config():
    def __init__(self):
        def screensaver(x):
            for d in [os.path.join(sys.prefix, "bin"), XSCREENSAVERS_PATH, "/usr/bin", "/usr/local/bin"]:
                f = os.path.join(d, x)
                if os.path.exists(f) and os.path.isfile(f):
                    return f
            return  None

        ALL_SCREENSAVER_TESTS = [screensaver(x) for x in ["rss-glx-lattice", "rss-glx-plasma", "deluxe", "eruption", "memscroller", "moebiusgears", "polytopes"]]
        #SOME_SCREENSAVER_TESTS = [screensaver(x) for x in ["memscroller", "eruption", "xmatrix"]]
        SOME_SCREENSAVER_TESTS = [screensaver(x) for x in ["memscroller", "moebiusgears", "polytopes", "rss-glx-lattice"]]

        #our selection:
        self.TEST_CANDIDATES = [screensaver("deluxe")]
        self.TEST_CANDIDATES = self.X11_TESTS + SOME_SCREENSAVER_TESTS + self.GAMES_TESTS
        self.TEST_CANDIDATES = self.GLX_TESTS + self.X11_TESTS + ALL_SCREENSAVER_TESTS + self.GAMES_TESTS
        self.TEST_CANDIDATES = self.GLX_TESTS + self.X11_TESTS + ALL_SCREENSAVER_TESTS + self.SOUND_TESTS + self.VIDEO_TESTS + self.GAMES_TESTS

        #now we filter all the test commands and only keep the valid ones:
        print("Checking for test commands:")
        self.X11_TEST_COMMANDS = []
        for x in self.TEST_CANDIDATES:
            if x is None:
                continue
            if type(x) in (list, tuple) and not os.path.exists(x[0]):
                print("* WARNING: cannot find %s - removed from tests" % str(x))
            else:
                print("* adding test: %s" % str(x))
                self.X11_TEST_COMMANDS.append(x)

    CUSTOM_PARAMS = []
    TEST_CANDIDATES = []
    X11_TEST_COMMANDS = []

    IP = "127.0.0.1"            #this is your IP
    PORT = 10000                #the port to test on
    DISPLAY_NO = 10             #the test DISPLAY no to use
    START_SERVER = True         #if False, you are responsible for starting it
                                #and the data will not be available

    #tools we use:
    IPTABLES_CMD = ["sudo", "/usr/sbin/iptables"]
    TRICKLE_BIN = "/usr/bin/trickle"
    TCBENCH = "/opt/VirtualGL/bin/tcbench"
    TCBENCH_LOG = "./tcbench.log"
    XORG_BIN = "/usr/bin/Xorg"
    VGLRUN_BIN = "/usr/bin/vglrun"

    XORG_CONFIG = "%s/xorg.conf" % HOME
    XORG_LOG = "%s/Xorg.%s.log" % (HOME, DISPLAY_NO)
    PREVENT_SLEEP_COMMAND = ["xdotool", "keydown", "Shift_L", "keyup", "Shift_L"]

    SETTLE_TIME = 3             #how long to wait before we start measuring
    MEASURE_TIME = 5            #run for N seconds
    COLLECT_STATS_TIME = 10     #collect statistics every N seconds
    SERVER_SETTLE_TIME = 3      #how long we wait for the server to start
    DEFAULT_TEST_COMMAND_SETTLE_TIME = 1    #how long we wait after starting the test command
                                            #this is the default value, some tests may override this below

    TEST_XPRA = True
    TEST_VNC = False            #WARNING: VNC not tested recently, probably needs updating
    USE_IPTABLES = False        #this requires iptables to be setup so we can use it for accounting
    USE_VIRTUALGL = True        #allows us to run GL games and benchmarks using the GPU
    PREVENT_SLEEP = True

    LIMIT_TESTS = 20           #to limit the number of tests being run
    MAX_ERRORS = 100            #allow this many tests to cause errors before aborting

    #TRICKLE_SHAPING_OPTIONS = [NO_SHAPING]
    #TRICKLE_SHAPING_OPTIONS = [NO_SHAPING, (1024, 1024, 20)]
    #TRICKLE_SHAPING_OPTIONS = [(1024, 1024, 20), (128, 32, 40), (0, 0, 0)]
    #TRICKLE_SHAPING_OPTIONS = [NO_SHAPING, (1024, 256, 20), (1024, 256, 300), (128, 32, 100), (32, 8, 200)]
    #TRICKLE_SHAPING_OPTIONS = [NO_SHAPING, (1024, 256, 20), (256, 64, 50), (128, 32, 100), (32, 8, 200)]
    TRICKLE_SHAPING_OPTIONS = [NO_SHAPING]

    GLX_TESTS = [GLX_SPHERES, GLX_GEARS]

    #X11_TESTS = [X11_PERF, FAKE_CONSOLE_USER_TEST, GTKPERF_TEST]
    X11_TESTS = [X11_PERF, XTERM_TEST, FAKE_CONSOLE_USER_TEST, GTKPERF_TEST]

    XPRA_USE_PASSWORD = False

    #some commands (games especially) may need longer to startup:
    TEST_COMMAND_SETTLE_TIME = {}

    #games tests:
    #for more info, see here: http://dri.freedesktop.org/wiki/Benchmarking
    TEST_COMMAND_SETTLE_TIME[NEXUIZ_TEST[0]] = 10
    TEST_COMMAND_SETTLE_TIME[XONOTIC_TEST[0]] = 20
    GAMES_TESTS = [NEXUIZ_TEST, XONOTIC_TEST]

    #sound tests
    VIDEO_TESTS = []
    SOUND_TESTS = []
    if not os.path.exists("test.mp3"):
        print("test.mp3 not found, the corresponding sound mplayer sound and vlc video tests are disabled")
    else:
        SOUND_TESTS.append(MPLAYER_SOUND_LOOP_TEST)
        VIDEO_TESTS.append(VLC_SOUND_TEST)

    #video tests
    if not os.path.exists("test.avi"):
        print("test.avi not found, vlc and mplayer video tests are disabled")
    else:
        VIDEO_TESTS.append(VLC_VIDEO_TEST)
        VIDEO_TESTS.append(MPLAYER_VIDEO_TEST)

    XPRA_FORCE_XDUMMY = False

    #XPRA_QUALITY_OPTIONS = [40, 90]
    #XPRA_QUALITY_OPTIONS = [80]
    XPRA_QUALITY_OPTIONS = [10, 40, 80, 90]

    #XPRA_COMPRESSORS_OPTIONS = ["lz4", "zlib", "lzo", "zlib,lzo", "all", "none"]
    XPRA_COMPRESSORS_OPTIONS = ["all"]

    #XPRA_COMPRESSION_LEVEL_OPTIONS = [0, 3, 9]
    #XPRA_COMPRESSION_LEVEL_OPTIONS = [0, 3]
    XPRA_COMPRESSION_LEVEL_OPTIONS = [None]

    #XPRA_PACKET_ENCODERS_OPTIONS = ["rencode", "bencode", "yaml"]
    XPRA_PACKET_ENCODERS_OPTIONS = ["rencode"]

    #XPRA_CONNECT_OPTIONS = [("ssh", None), ("tcp", None), ("unix", None)]
    XPRA_CONNECT_OPTIONS = [("tcp", None)]
    #if XPRA_VERSION_NO>=[0, 7]:
    #    XPRA_CONNECT_OPTIONS.append(("tcp", "AES"))

    #XPRA_TEST_ENCODINGS = ["png", "x264", "mmap"]
    #XPRA_TEST_ENCODINGS = ["png", "jpeg", "x264", "vpx", "mmap"]
    XPRA_TEST_ENCODINGS = ["png", "rgb24", "jpeg", "x264", "vpx", "mmap"]

    #XPRA_ENCODING_QUALITY_OPTIONS = {"jpeg" : XPRA_QUALITY_OPTIONS,
    #    "webp" : XPRA_QUALITY_OPTIONS,
    #    "x264" : XPRA_QUALITY_OPTIONS+[-1]}
    XPRA_ENCODING_QUALITY_OPTIONS = {"jpeg" : [-1], "x264" : [-1]}

    XPRA_ENCODING_SPEED_OPTIONS = {"rgb24" : [-1, 0, 100]}

    #XPRA_OPENGL_OPTIONS = {"x264" : [True, False],
    #    "vpx" : [True, False]}
    #only test default opengl setting:
    XPRA_OPENGL_OPTIONS = {}

    XPRA_MDNS = False
    TEST_SOUND = False

    TEST_NAMES = {GTKPERF_TEST: "gtkperf",
                  MPLAYER_SOUND_LOOP_TEST : "mplayer sound",
                  VLC_SOUND_TEST : "vlc sound visual",
                  MPLAYER_VIDEO_TEST : "mplayer video",
                  VLC_VIDEO_TEST : "vlc video",
                  }

    def print_vars(self):
        print("\nCurrent Settings:\n-----------------")
        print("CUSTOM_PARAMS: %s" % str(self.CUSTOM_PARAMS))
        print("GLX_TESTS: %s" % self.GLX_TESTS)
        print("X11_TESTS: %s" % self.X11_TESTS)
        print("GAMES_TESTS: %s" % self.GAMES_TESTS)
        print("VIDEO_TESTS %s" % self.VIDEO_TESTS)
        print("SOUND_TESTS %s" % self.SOUND_TESTS)
        print("TEST_NAMES: %s" % self.TEST_NAMES)
        print("TEST_CANDIDATES: %s" % self.TEST_CANDIDATES)
        print("X11_TEST_COMMANDS: %s" % self.X11_TEST_COMMANDS)
        print("TEST_COMMAND_SETTLE_TIME: %s" % self.TEST_COMMAND_SETTLE_TIME)
        print("IP: %s" % self.IP)
        print("PORT: %s" % self.PORT)
        print("DISPLAY_NO: %s" % self.DISPLAY_NO)
        print("START_SERVER: %s" % self.START_SERVER)
        print("SETTLE_TIME: %s" % self.SETTLE_TIME)
        print("MEASURE_TIME: %s" % self.MEASURE_TIME)
        print("COLLECT_STATS_TIME: %s" % self.COLLECT_STATS_TIME)
        print("SERVER_SETTLE_TIME: %s" % self.SERVER_SETTLE_TIME)
        print("DEFAULT_TEST_COMMAND_SETTLE_TIME: %s" % self.DEFAULT_TEST_COMMAND_SETTLE_TIME)
        print("TEST_XPRA: %s" % self.TEST_XPRA)
        print("TEST_VNC: %s" % self.TEST_VNC)
        print("USE_IPTABLES: %s" % self.USE_IPTABLES)
        print("USE_VIRTUALGL: %s" % self.USE_VIRTUALGL)
        print("PREVENT_SLEEP: %s" % self.PREVENT_SLEEP)
        print("LIMIT_TESTS: %s" % self.LIMIT_TESTS)
        print("MAX_ERRORS: %s" % self.MAX_ERRORS)
        print("TRICKLE_SHAPING_OPTIONS: %s" % self.TRICKLE_SHAPING_OPTIONS)
        print("XPRA_USE_PASSWORD: %s" % self.XPRA_USE_PASSWORD)
        print("XPRA_FORCE_XDUMMY: %s" % self.XPRA_FORCE_XDUMMY)
        print("XPRA_QUALITY_OPTIONS: %s" % self.XPRA_QUALITY_OPTIONS)
        print("XPRA_COMPRESSORS_OPTIONS: %s" % self.XPRA_COMPRESSORS_OPTIONS)
        print("XPRA_COMPRESSION_LEVEL_OPTIONS: %s" % self.XPRA_COMPRESSION_LEVEL_OPTIONS)
        print("XPRA_PACKET_ENCODERS_OPTIONS: %s" % self.XPRA_PACKET_ENCODERS_OPTIONS)
        print("XPRA_CONNECT_OPTIONS: %s" % self.XPRA_CONNECT_OPTIONS)
        print("XPRA_TEST_ENCODINGS: %s" % self.XPRA_TEST_ENCODINGS)
        print("XPRA_ENCODING_QUALITY_OPTIONS: %s" % self.XPRA_ENCODING_QUALITY_OPTIONS)
        print("XPRA_ENCODING_SPEED_OPTIONS: %s" % str(self.XPRA_ENCODING_SPEED_OPTIONS))
        print("XPRA_OPENGL_OPTIONS: %s" % self.XPRA_OPENGL_OPTIONS)
        print("XPRA_MDNS: %s" % self.XPRA_MDNS)
        print("TEST_SOUND: %s" % self.TEST_SOUND)





