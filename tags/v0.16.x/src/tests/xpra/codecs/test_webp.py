#!/usr/bin/env python
# This file is part of Xpra.
# Copyright (C) 2014 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os.path
import sys
import time
import binascii

from io import BytesIO

from xpra.codecs.webp.encode import compress, get_version   #@UnresolvedImport
import PIL.Image            #@UnresolvedImport


def do_test_encode(rgb_data, w, h, N=10, Q=[50], S=[0, 1, 2, 3, 4, 5, 6], has_alpha=False):
    #buf = "\0" * (w*h*4)
    #buf = get_source_data(w*h*4)
    def webp(q, s):
        return compress(rgb_data, w, h, quality=q, speed=s, has_alpha=has_alpha)
    def PIL_webp(q, s):
        raise NotImplementedError("fixme!")

    TESTS = {"webp" : webp}

    for name,encode in TESTS.items():
        for q in Q:
            for s in S:
                #print("test_encode() quality=%s, speed=%s" % (q, s))
                start = time.time()
                quality = q
                speed = s
                if s>0:
                    speed = s*16.7
                for _ in range(N):
                    data = encode(quality, speed)
                    #def webp_encode(coding, image, quality):
                    if N>1:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                if N>1:
                    print("")
                #def compress(pixels, width, height, quality=50, speed=50):
                end = time.time()
                mps = w*h*N/(end-start)/1024/1024
                ratio = 100.0 * len(data) / len(rgb_data)
                print("%s compressed at %4.1f MPixels/s  %4.1f%% compression ratio : %4ix%-4i to: %9i bytes (quality=%3i, speed=%3i) %2i times in %5ims average" %
                      (name, mps, ratio, w, h, len(data), quality, speed, N, (end-start)*1000.0/N))

def test_encode():
    img_data = binascii.unhexlify("52494646081300005745425056503820fc120000d03e009d012a80008000000708858588858488028219c1d32f2755672a4e67f137ffdd8cfdbe9d39fdfa9fe7536e0afc2bf32fc1d7ad7dcff573c95f595a85fcb3ede7ea3fbcfee3fc65fe03bcff923a82fb13fd5f8abec36da3fd6ffcef505ef07fc5ff01e2dbfee7a0df5bbfe77b80ff32fe61fedbd54ff37e141f75ff4bec03fd1bfb67fd6ff3df98df249ff17f99fcdef6eff4cffe4ff35f00ffab3ff2ffbc7b5efffff73dfb85ecb1fac7ff87defcd6e1ccb7c52211f324fad197772f07adff320c8a6e3c954257aa7d1d37d2e3dfe692a22442982085e1d214d44549fe4b87b9af1aa705e5618b9a6cb936cf8d950e9d08f2262f84562f4d3a9ec827e7eebdd7bd95ed9637c83e991eb4e61d31d8688edc9f6dae95789cf8178a989a30ce4b3dbbf88671461109594162d6878d75e4198e04d7225b1a17cbc83189d0aa0ebf3290be2b020fb221914f0e75a2fe86661e2224636ecb04da2e078107bdd1bd79a073912f2255ba4a9e3f2e5cab360885056c7ff617ff2d128ec21630baa994e7ff19467493fa443061439801cce618020b0a60e239dc6dcc4e6e9d21ebaf822697b6731edf7766e4eb449b6870cb32cd316120ffff112cb5ab755ac0a728d7cf1c882794c50df5bc848870054e346fb04c426a5dee7e50f9b6ca043a4d5819bf7500df3dd5eb43a5eda5f766b8733de67b21d802f45d051870127abbb9a0fefffe1381f5747c039fff921bf9e7fd5e69a3ffc9bc2fee2c690ba401704f7ef1bf3eacdce82334409ded4675f173a1c1c417f03fc220a554fd54f4dbd328e45139063a58698f766f82fcd2b591549e20e23bf425c47fc7a1fcae2dffb04ecb2c8076274c9ff456233f65e2f6abea766fd6f30cd8596d9dde7f491bf36955ba853b80b7dd7d2db7466230967b8035373285b84630ef4a084d1388367502f970a662a37561708b6b7d392c1d959fca8dd88a5bea53c69fc239e39cf0a500d2658b751e67d12f185eadb6664f2b58573cb7880f61f8b54e7f66bfd6dffbe896767bfe61931a97f9442fbfee2cbb9ee91a4d215960754ca00bd922c191aa1f949535d7e26a5be8002add5cd8b1b8a7f43e3851ad08bf00b5ff7ae99d3d3474cd0388168aee9775e50bb7d0fa08327b3d04bc2f77efa0d157e9c5d32a155c4714a97531ffc1b55b1363e825bd814d13ef96cf72363ffefc44357dcc6283f4d30ff3c32adc0e7ffe733b95da5b3d7bb9ffa67f6571d35612fff109509de5da5afbfdb95896e2b2e51faad29f41787a55c068a62e011f1afc72e709d7f2faa2feaf7f46e64fd6514d34ee1c0a11eac027fc578c58d02dccabf46a6ab2b2eab608bd1903e3d882ea978a6d80304a127a0e8bee556567df49447780352611f4d253c4ece8fcc8efdb1d6f946fff011c9e981c8f795c91f26da2ddfeece906ca45832d4201b17e5e2ccae32e75871588de9adbf75fb3577f9d4ad9f0135bbf8624de5ff880a1c293c1c4b94305366b09e25fc07ebb23d4920988b08d39024334650a9d1576a8955c5d1bb5ff56f9a6b3743fd39f8f04f10835e088a68f03d11d0c11af2939721065c8c87ffa6a5e964ac9c914684d9d4489a42558716f07cb7a781d6342cf8c42b07414a8322ceda3c88df2691fd146b6405116000f21294a9c1303491eb1228668ed7767f72ca5a4b5e8b9c09277adac135353aadf56d858d240cb91efcb37e68e3b687dc74d8fe4d9fdf41f0b435839c87d9971eff3acf1d15c477d84e3e01231b174f16e4d1c84a12fe9d9e7acd3256d28b32e751641ca25663eda61d903a00d2141c16d9e2a9a98f2dc6776db2f2dfc1e72b97a5142dc347b48e23ae9706311e9e987f5543af8cf2983c2cd1be96d2ef46fec81105a1c92b9e6d03631e0201271437201299b73d6f8733bc6fefb31934d8fbf6f6f900e2809f05a1643364566c6abf94f96095e7cd5f47b69f891c0ecb906a706106010730d01a20460fd122a9cad3471a0a2f85918883ae0e6f43fe6ae84b0e23dd80a57f50de5bfb5da6f0f2a650971267b7d2925ee5a16d387a2bbc441443f66da408991a23cf13df96615385430c544f62cf0bb4e0da8c663e78d868d4688dc1175a01b5defa2720075ab17ca74084d4b9ee325f33a11ab969742857ec5461b9050f0475983f94e6b6cc27d04e01313a52a9cd8f949925b781a4484675499badbf8b9904f31ba5cc2266820e65662688fa65e3d47da990098933ea095642c430c8120f80acf1bd7b0fc44f1f4cf7d4610efae786c658a821f4a0ef142f546455692a296b8dcc28c57c4aec85af4dfe680749c3065ce2ee8a716f2b1e518fb01ed4b76b5ebf225ec13877a71e614e25c4b4b72b068a68e4fcf5eee6c879b22c4dce83c6f33eb8b144f4a2ba134b962fdc8b42b50e3ca19bcf431a7d746cc681c5cb9c789beb4f3373029511b2a62c038cdc1ff612a903d2a6242fc75ecda5fbb6b830f3f09c0589a6c9e0fe162b5736b957073931df627e0a95593dded2f919f96c281458b75f16f71bd8721ea97d45fd9be3d4ba97ef1e8478b25172f3d8e2f35cae99b96daf13d060c96c1901a6e42a18bce7913ccac787778c970ab41e3489e5d37ebefdde1ae28793d6129f01e79bfe8f71ef9e2fba6fef5184c6f0878ff3fceabf97ca7d1552d623b980cf69409a0b8ad241ef855f79c2df32b66a26730f03124c04f56af74c3bc5c8b7050982caf44cb23a3a12ff25305d98556d854e9578caffa14f30317b784429aa6fe4521f16b179ac8724a78fcbc2398676eef4809fd47ba160beb3008b55403374efe07d3fbb1bfd25a2771d8b414dae124561355d39cbb6e3a919fad83f12c83ebfda741d5a7f0976ca032a194fc3a2490dbe9c373e1efc555175979283dc2f22b7fea0e3c0139dea1e60865b88d156907b738ce1896679c1156f348c3a71f84ed748d8ce7f61c2f01073848ba043cdf4c46b0237c9bf5f7c58a02ee25f1fdadf45e3d5d98f93e2211263e07b368a76a9b8cadc0878c48d591e14693de1e8d4efc192b4235cf5f54c191e39ec66c2b59a4b36b4a38961a60d7f20b6b038c50468cf6ab7105ef7c5bb5fdf855c2ab9be89d39c1c38394701d5eea1e62ffbc9b41b6b3fb5d9a15316f05aa31fa0791ebe7feebbcbf8a1196372196794ca47a9f361aaccfc998cf9273fc3ece5b38944dd276b0c45c2c97b749b745b84752cca1f9f8ecfe0041023f8d5455f86745f6d7f0343a7951524f4df4cc5b9314bf0df650d43c006a5dd6dcb75761d7603150fdadcdc100c7e84c641157b80b4688c054baafb0ac8f79a19728f473d4a6491d8cc940a9985b91f731f79677f30f982f615f5d1e8b710a04a3cec757477c7903f39ba92a1815571990770813ee970afb080f0d99d8888b59157900af8ffc54f117b089a2d9ff99e6b1948a7a2bfa779cd7eed737c911020d2281a833d70a5ead5a9625786570cd7d4e834f6d6ef5c16ddf88be427eb417f098532175f7fa1e9858c5c3e75cd5ee8733db3830116fff0669fcdd3fc1aaabbd9d65f2fb15ae2d142ccd1452c850fc6b563880e35da8d6cd937b263699c3b974151aab748eab8922b3478531b43b4a505af8c2de2a2f660d9a5e37aefacfb6afa5d981a8c70a6f04b76197261ebb0ff3328ed056ef9c24ae8754e0a3f42d23d2ff7f6e8566b6d91dec01df4c272479593b9a2b6519ec16ffa83cbed670867aee5d806d75cd6bd4f9bb47e4447a2439619f2edf1f913632617df30203af0251fc82455fa639983e5332e44f9b00bb66afec61dc21cbda5419bce84fd1ff55f845a9063ac622b451d8465e7e7d893c3565b5dd06e49fe6cce94f5edb3ef441ec8af35fa69681799ffee9462f3cd7eeb9be83c411ca2ebeca8a42b8cd5627f6e25a3875a9e12784e259c1844f4b7b3a582147cce8c32553c25b75cb727758fef364cb0f687330601b9ac8eabb67b426c1b4348d64b1578e79c09a4c5d971e3d5c4834e4245ec778f05e5423183a9b3415a115b6fa910561c053f41a57c67a23578ed3b45b63be6433fe51444e0fe2d764fc1655af28918aaa87fc2f926d01ca76de6451287abfc5b3197ed971a0cdbc35f6d39f82f497a7c9c5ebe757e00182941de76f22cf3be0d835ca1d60e33b2def7ab1d4760dca69aabbcd9868bd05e748c3d49dc74f2d9bc04e37f676e67bfb086efb6c6cbf4127ec3011b70a9f483381dec0018c1a1b3724aafcec8a0973bea7fd31fa7cf50c3fa99c8a8123ef0ef92d4cda395d1915b02693d375d576dd29ae5280b454537a5b6009ab1137d296c47715398e1038fc0e7f01b2b034fd1361717416e75157d7e5b14c0f3825170708c009b86a25b168935d3c7609f6f47f6f2035c02c78079bd45c6e28c6b71e8c0e539fe8a2c2f58e1b072b0109318e5ce0dc7eb3caa10eefa1c5a3711fad493b5c7ec999d27e657369e439b4d08302b8aee65f8d73db79d9dee1696232359fe7f68d196c683787e278221228d5d7253f0e7278a0947e073ed2ac4559ae65247a98736793b9fbed54d3cbbf8d215d95010fe2ba7f0c6c16f38b7cd152f04bd39bdd681ea7ca6372cf33f1c8ab544d97c03594b2f3df9b74b889f070cccbcf7d2ce63a096beb28785705b74e54139def95b0f210c7cfb1e030ab4e39fbd0866be0dfe4bf6ba43c6ef34d7eefc770dc76326d0f8289323044c38e78e5d08fdfde4dae74b47ea2fd38c2e847340d6d2c5ad71281c8687320cdffd7da37f2b1bd7a26d3c6df60dde0ad5afd201c237f203c473417aff8f551b7d49575a086910d59e65011661fc2ea0f54b5919b26dae1a1e9b7bd8b46cf984637b9c70da2c5b6a7297fd6420f16cfef7f839dc0e97be8a80729fcf2cee4e0ffa440b0d36b6828cebf2618de96f70340b317d524d0d701bef4624580bd576c109f46083226ab7b163280b21778f371b32b186ef4005383538e5efff8b09ee648e32d79022ed5f305f0262d20a434c7d6463b520430c480800af5d3e880f133d0781a2c61b358519de88003b1c843ade2f1201ba10b83d57255b8ef70663c139b27609240580d4b8168c6ac4f014d6032209928bf5fb65a293f1cacfe3491313dd683040f97452c9c48efd6365c152a74e94156f8cba544388ffad737199d9269d2447821c88133da943fd56663ce10f2574d53c85190bb7768aff7189548fe817726c6ed00c43a383c34955cd09443a35326693524f65e94048d9d13740d39d0b27abb3b111fb0c91779d5913b28e61fff965999c6662a48a0e4643834f2d6ca8e5098de1520b5efcb7b0bd34f36388b5b23a35a7a50b893eecf3cc7396cff51fe1cdb1c9736c40db11b2022a65d43fed9189cf9b6d24d88eaa613949425030861fe846cec72bd5d1329167cb2b134518959485587e18d98aba1b10095673ed69e1458410337dce7d02a1ce49116e3959e897033639f56711501298fb4ce63280bfb51188590bad6654f823cd4e7416ec031dd3268125db01c2867780427d309208971e6cf9afed31e91f0c31a6b2ea4f9992ba582cc7d221c55436637fe3145e4cabdb051320bd52cc5805fdcae119db659d90ee08f35f4009c9e1b578e863f8720b824134175fc7c757eb0318e0bcff64db8ea99d8b7ffe59d19ba0796a3ff94312ed0d26549d6e1e3b2619ea0c4b529b19a9b1ca82740d38437add1d6bb0ea4c502774f539f0a34193ea9108d7860cb0800e81b94d0c966f1893d102e91bf22730d7a9b8768c7abed66016cbc430f00163f5f3b5ebba2f0eea0ba8da054dd18437bd4ca49725fe6fb06f609ac4829b158d4c03a4952a2226f378e50130da7625021260533393929024cecc98564d0a0f5179e25a444f31b5bcfbee042c4310816604534b42ae39b0c337a42c4c8f6595a6690fa47d698fcfa8c81a6114ab5149e29a77f57db5af5fe974fca5fd676a1d18e47e983a842abb4d3a24366993cec14790b44481dc7b98cd8bf023eb2bc80ec58c6ed80c406c79b89f8003ebe641731864ec091464367a30405b7406713805f60038037b94d403181e2ce30ea92eb1f1405ed43db6704be529f94b3fa130eb13e31554788fc996d08ae2b50cdb2ce06ee60afd6e404863069cb7229041a9a00bca53347bac08c2a60bdc708916acca8176af5c30c80e3501a98ac99535a0324e8c9ae9be365c64212677cf11f7897f852a8f240135f9f7622baec84b962285e65503bda3bd0e5d674ee36b54c9eac921ee7ef6a7c8e169d14d034223cd55ab82baa1700467c42fd7954148032d919e9c00e247a26364046f09e86cb9e24b48d7eee1949e698b0731033c79022715a5b3acef98dd3ab4e6e0f9f32c0bb563c31c1d9f700694623bb6881c184b1bfdbb2fde4552da930fd0b7a247dc121884709258ea5ef46ee15d4a5bf1f37a274432ae1ca0a54fe12b43ca9d49ec25f300cd3021dcc4bc651265f7c2fb4f61941b360a70371f4eb3cba13480cf3c5b1b28c3e59fc8f6f0990c46f033e2643736c00de293fb65acfb9ad54beaad5b4b2ef47cec5c8d804ea198646e61bcb3e0e3a6ae1f63834470f228740d0c12eb4860a5a962bcb74d62c66ede2a2ac5e845eb6a23bf6726b027eca8c599719e43c910bfba285fd0ad1e5184623a1b47691c3105d5906da48ea8d929ea89a4801ca3d2586cf4a84732c0750a94b1d489f9c6c3205be384e0ccbd41d70b1d198a1aec92b7133551e7948932a900494b61154c4a86dccf37de4be3d6a6e7508aa288a3c1e627cb942cd11e8fe27a75e070686b90846a6ac7f460ceca0fd032a23da8730b11ca3d417565ffc1c82b23f1aa0432037911b27a04468ee14bb69928074e834ef5abab3110ec3e7dee9070000")
    buf = BytesIO(img_data)
    img = PIL.Image.open(buf)
    img = img.convert("RGBA")
    rgb_data = img.tostring("raw", "BGRA")
    w, h = img.size
    do_test_encode(rgb_data, w, h)

def test_alpha():
    #webp seems to have problems with empty alpha?
    w = 640
    h = 480
    rgb_data = "\0"*w*h*4
    do_test_encode(rgb_data, w, h, N=2, Q=[0, 50, 100], S=[0, 3, 6], has_alpha=True)

def test_files(filenames=[], d="", extensions=[".png", ".jpg"], recurse=True):
    for x in filenames:
        p = os.path.join(d, x)
        if os.path.isdir(p):
            if recurse:
                test_files(os.listdir(p), p, extensions, recurse)
            continue
        try:
            img = PIL.Image.open(p)
            img.load()
            print("img.mode=%s" % img.mode)
            has_alpha = img.mode=="RGBA"
            if not has_alpha:
                img = img.convert("RGBA")
            rgb_data = img.tostring("raw", "BGRA")
            w, h = img.size
            print("testing with file: %s (%sx%s)" % (p, w, h))
            do_test_encode(rgb_data, w, h, N=1, Q=[0, 50, 99, 100], S=[0, 2, 4, 6], has_alpha=has_alpha)
            print("")
        except Exception as e:
            print("error on %s: %s" % (x, e))

def main():
    print("webp version: %s" % str(get_version()))
    test_encode()
    if len(sys.argv)>0:
        filenames = sys.argv[1:]
        print("testing with folders/files: %s" % ", ".join(filenames))
        test_files(filenames)
    test_alpha()


if __name__ == "__main__":
    main()
