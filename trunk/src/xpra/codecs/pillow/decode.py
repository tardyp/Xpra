# This file is part of Xpra.
# Copyright (C) 2014-2017 Antoine Martin <antoine@devloop.org.uk>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

import os
from xpra.log import Logger
log = Logger("encoder", "pillow")

import PIL                      #@UnresolvedImport
from PIL import Image           #@UnresolvedImport
from xpra.codecs.pillow import PIL_VERSION

DECODE_FORMATS = os.environ.get("XPRA_PILLOW_DECODE_FORMATS", "png,png/L,png/P,jpeg,webp,jpeg2000").split(",")


def get_version():
    return PIL_VERSION

def get_type():
    return "pillow"

def do_get_encodings():
    log("PIL.Image.OPEN=%s", Image.OPEN)
    encodings = []
    for encoding in DECODE_FORMATS:
        #strip suffix (so "png/L" -> "png")
        stripped = encoding.split("/")[0].upper()
        if stripped in Image.OPEN:
            encodings.append(encoding)
    log("do_get_encodings()=%s", encodings)
    return encodings

def get_encodings():
    return ENCODINGS

ENCODINGS = do_get_encodings()

def get_info():
    return  {
            "version"       : get_version(),
            "encodings"     : get_encodings(),
            }

def selftest(_full=False):
    global ENCODINGS
    import binascii
    from xpra.os_util import BytesIOClass
    #test data generated using the encoder:
    for encoding, hexdata in (
                       ('png',      "89504e470d0a1a0a0000000d4948445200000020000000200806000000737a7af40000002849444154785eedd08100000000c3a0f9531fe4855061c0800103060c183060c0800103060cbc0f0c102000013337932a0000000049454e44ae426082"),
                       ('png',      "89504e470d0a1a0a0000000d4948445200000020000000200802000000fc18eda30000002549444154785eedd03101000000c2a0f54fed610d884061c0800103060c183060c080810f0c0c20000174754ae90000000049454e44ae426082"),
                       ('png/L',    "89504e470d0a1a0a0000000d4948445200000020000000200800000000561125280000000274524e5300ff5b9122b50000002049444154785e63fccf801f3011906718550009a1d170180d07e4bc323cd20300a33d013f95f841e70000000049454e44ae426082"),
                       ('png/L',    "89504e470d0a1a0a0000000d4948445200000020000000200800000000561125280000001549444154785e63601805a321301a02a321803d0400042000017854be5c0000000049454e44ae426082"),
                       ('png/P',    "89504e470d0a1a0a0000000d494844520000002000000020080300000044a48ac600000300504c5445000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000b330f4880000010074524e53ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0053f707250000001c49444154785e63f84f00308c2a0087c068384012c268388ca87000003f68fc2e077ed1070000000049454e44ae426082"),
                       ('png/P',    "89504e470d0a1a0a0000000d494844520000002000000020080300000044a48ac600000300504c5445000000000000000000000000000000000000000000000000000000000000000000330000660000990000cc0000ff0000003300333300663300993300cc3300ff3300006600336600666600996600cc6600ff6600009900339900669900999900cc9900ff990000cc0033cc0066cc0099cc00cccc00ffcc0000ff0033ff0066ff0099ff00ccff00ffff00000033330033660033990033cc0033ff0033003333333333663333993333cc3333ff3333006633336633666633996633cc6633ff6633009933339933669933999933cc9933ff993300cc3333cc3366cc3399cc33cccc33ffcc3300ff3333ff3366ff3399ff33ccff33ffff33000066330066660066990066cc0066ff0066003366333366663366993366cc3366ff3366006666336666666666996666cc6666ff6666009966339966669966999966cc9966ff996600cc6633cc6666cc6699cc66cccc66ffcc6600ff6633ff6666ff6699ff66ccff66ffff66000099330099660099990099cc0099ff0099003399333399663399993399cc3399ff3399006699336699666699996699cc6699ff6699009999339999669999999999cc9999ff999900cc9933cc9966cc9999cc99cccc99ffcc9900ff9933ff9966ff9999ff99ccff99ffff990000cc3300cc6600cc9900cccc00ccff00cc0033cc3333cc6633cc9933cccc33ccff33cc0066cc3366cc6666cc9966cccc66ccff66cc0099cc3399cc6699cc9999cccc99ccff99cc00cccc33cccc66cccc99ccccccccccffcccc00ffcc33ffcc66ffcc99ffccccffccffffcc0000ff3300ff6600ff9900ffcc00ffff00ff0033ff3333ff6633ff9933ffcc33ffff33ff0066ff3366ff6666ff9966ffcc66ffff66ff0099ff3399ff6699ff9999ffcc99ffff99ff00ccff33ccff66ccff99ccffccccffffccff00ffff33ffff66ffff99ffffccffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000023faca40000001549444154785e63601805a321301a02a321803d0400042000017854be5c0000000049454e44ae426082"),
                       ('jpeg',     "ffd8ffe000104a46494600010100000100010000ffdb004300100b0c0e0c0a100e0d0e1211101318281a181616183123251d283a333d3c3933383740485c4e404457453738506d51575f626768673e4d71797064785c656763ffdb0043011112121815182f1a1a2f634238426363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363ffc00011080020002003012200021101031101ffc4001500010100000000000000000000000000000007ffc40014100100000000000000000000000000000000ffc40014010100000000000000000000000000000000ffc40014110100000000000000000000000000000000ffda000c03010002110311003f009f800000000000ffd9"),
                       ('jpeg',     "ffd8ffe000104a46494600010100000100010000ffdb004300100b0c0e0c0a100e0d0e1211101318281a181616183123251d283a333d3c3933383740485c4e404457453738506d51575f626768673e4d71797064785c656763ffdb0043011112121815182f1a1a2f634238426363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363636363ffc00011080020002003012200021101031101ffc4001500010100000000000000000000000000000007ffc40014100100000000000000000000000000000000ffc40014010100000000000000000000000000000000ffc40014110100000000000000000000000000000000ffda000c03010002110311003f009f800000000000ffd9"),
                       ('webp',     "524946465c00000057454250565038580a000000100000001f00001f0000414c50480f00000001071011110012c2ffef7a44ff530f005650382026000000d002009d012a200020003ed162aa4fa825a3a2280801001a096900003da3a000fef39d800000"),
                       ('webp',     "524946465c00000057454250565038580a000000100000001f00001f0000414c50480f00000001071011110012c2ffef7a44ff530f005650382026000000d002009d012a200020003ed162aa4fa825a3a2280801001a096900003da3a000fef39d800000"),
                       ('jpeg2000', "0000000c6a5020200d0a870a00000014667479706a703220000000006a7032200000002d6a703268000000166968647200000020000000200003070700000000000f636f6c720100000000001000000d8b6a703263ff4fff51002f000000000020000000200000000000000000000000200000002000000000000000000003070101070101070101ff52000c00000001000504040001ff5c00134040484850484850484850484850484850ff640025000143726561746564206279204f70656e4a5045472076657273696f6e20322e332e30ff90000a000000000d040001ff93c7d4040977c1f20106c7d404049fc07c20c0f900c07c8040080107c03a0c010c0084070707c0f90140f900c03e1040057f0305c1f38483e70907d40a0d5baab30c1897bf0b2ccdf607c03a141f38487da0a003cf0e13572c01e2b616dfc1f38483e70907d40a0d6a9ce90c459c710ff00205bfc3ea1187d41d0fb44411e2c3e4379101f73b3459b6a61066ff7f07649d884d89d90068baf1b3327f143c7a1cb72bb9df9494fa4cd8b4aec09fc7da211f68943ed1300a1613b5a6ecf3266bc9eaa4aab16e2717f77070d476d1ec90c7455f4761dcf465f302db51faec9e1b5c1cc854f250334e36e95a9fc3ea108fb44a1f689012abc11315c3e36f7995c0c44a9f3a5917df22504861216db8faca9431194af1b32b16847435f00b2817291621b99fcd79e5cce3c7da7b1f69fc7e08a026d03038ccfa865709f8fa0ebea3622eaf4f68a3672f799b0c95f3f93d793feb3ec88a21c6faa1ad7d154b21e40d1788a2442808f0594ef8d945d2f5fd17f95dc4129d3aad41246afaff2b5b61dbcd75a8f85056654a1f8eb6276d776c82321ab42845d07fa64283529ca80c46189524f52f8dd6479ceabeb07916d90a1740e9c1455434770c78797532824a27bb3df6265724c4e34a5d1c7ef87b2810eebe19104476c5b1abc42d1f9c52e4ac8902cba5a676f57293bc7119de8d7f6f821b1edfc7da873f0448fc1240173329ccc8cc1e00bf57e27208b6c7d1143b43bd351840f54f08f51bdace2d423e66b6f24cf61fae9a247158f196c44b41eb2a8f9f1f960cd4f4bd7cbf4f2be8992c7f48a83e2c6f182eff5a602c57ce86daceec1bd379018825ec2264078e7dc7f7f6a496115619cde81b18a829e8df8a5b5e188a0e7f23c4fc728edcc78cf77ba2b5c0df967f302adc347b999d512564cebd7d89c66fc579a8dd05547a181e4be9079acb1d9aa0b160981da8d3c38f451fbdfc217689831681d206d039c4a36f7909fb1d11d7e978215cb03a9c0e3bc7da8b3f0449f9a580198f765dce94872bb3e08a4fc1c743931627796b4efc0012ae795767e9e08e6f4a4f16bca96d0581cb5e09f10e068ed53c26297d927cc57d03c38beb213b0ea513e82b4caf48ac318401d37f34e79411c323bbb89509dfe4b4e0aa036d87a46dff1e529788bc2048fc28907f04a1d85024d15a22e1fa3ecb1d4d5264f7d72f4fa7d51851074efb387f0760929f7134e14472776446154ac013368e3711f63d6392f856197dcc74af2cf37241e89a893c8a0e6704903c92f86f4f9a83fde7d961d1505efb7f589c06c46d06d1fb4b6cded97310dfcfc2fe9f8682cfceff0010e715ca18e9343f215b1b4f38cd8c23c020f122af4cc1b9d265644f425d9279a479e9cdea4eb33864945cca8bc7148026429e977a508a39bf44f0ea5e1ba474ad9131083f77af6394e471ff83e77c3465f8a37c98680fd9443662d3ded723aa65c3bf8f6f4fff045b1ef10e68b5f53b78ef6d863aded77d5ce9fc5db54b37b2a4e22bb8aefc776149ddd58b0292e9dccca564ac2cbe802b1ff5c6530c243fa50fa4043431f982604881dc430471d64a4a247d4cf58d10a1b8422509205df5a087468f25c6798329961a9ad22f1ed39782673c4c6ddd2f12276ee794063a73d8208c92708b37a5c00e64be8ee21c639511854f24636ea5d7896e6de25b81ab6e2ba7e3d494b2f1f6c812143a51c3bcd60e3665cab9316af52befe64f6040d0d6a3254aa6232d3e085260a1ff650110ca5e13ea208e46e1c18a0f1e8ecd702bb7400687b0b9a64b52b63ee8653fc2681eba192ec26449c155f4c0bc45340341f0552ffe49e9ff2743ee6b3c81c5e79d91e71af4b6e1be023879e6d294fe45e20a7b06a1c2c4d79b3974a9a02347d55a2bd6006c6eb5627af3105cbf106f1aaf75efb9d75f7102339b1f7e67929cfe7c94fcbff4b603b347cd61babe2af40ee461416152f1704152af09f0a2a32e6c21e43ad0eb8e3917d776687a80ac0ad691c6f45459d800ca65dc0cbe187fc0ad61d33a0d90404a6491ecb77a903d90f35135211934a060c11096eea69b989383ed43f71834dab91fda63a8dccf9b39a85d5df94a59b6a88bde98f95ca7a037a46023efb85e2230cd5d4ee126038cd43f26f4199532e48eaf6fb88a2ea710e9ac84c8631aa5ae3132c23efb223b77552b7fbac317b472744c1bea68f8e8963bf20a4341383a2eceff6186eac2bd07a6cd7ecbed28557288fdad0d2f72172ce71237166b9d1b6fc692bafce66ed62754850df9210de6b558eb5ed329ae1ae8c1d83c2a7abeeb4861593cb9aa60c3e685c41716c63ee9dcc197078446346440f1bd385df84935829bf5554afda187344c3c1f4d214479384651ea15c1eb08dfaf52941d61a39fc8755b35b8eea0f220467ab36b9c1fcfc2fa9f8687c7e1a1203625a30755cc1c5536012034f6376b5a5315f867c613c12ada7fb95bdb6b93f41a727b238d473c64060f59e99f81927422f7627504e02f34b17b2ca62fa85e5c17a87726d0a91996e5aeebc4224f26bdbdeaf35da463ebc009dc29ee8fb9d003b6282f515241df887c2a3df30ee0332ec78f672ca29a5f6893bb051b86763ae80214f2e1f3a1765380691d9836a8f8ab1e7c735fcc55a15d405f6eee202ec968f3c9bcc98cee2df70d509ab1e54578a79ef982fbfaeb5d2a6c1e060a1f5221c5ce7bf26bc00b5da7a1bcd34638dad21b0df045591f5090bd74fb2dff3b4e95b91091b573ddb5baa67ce3bd1dd0cd3330cea9ca65a0180633cdf31d2b721c22789aa7005af0db25e627bbb9b6662f2f54b3715cd1059f210d33a9711ce012596c3d7b47322a14577ffcdbd0ddf9a67729ba4665fd9e788b224dfabd912fde48c074d2326bdbc749018afbf777b9898a4e7c60901f2d288aa6e6a8b6073afd740cc98e50d9e8070f1afb0ca7657e17b653f8f3725e1f0b2a48f4572d6f589a11ea8aba88bbf7ec76ce923040aab560a78b61237ee74b17691e5690b45478229f9bfbca60f4928c6e255933e8c934fc68e4c8d087812b9fa4a63d0b44a124babc5d3646e6dc5eafb08452e359d369936a0c8eb75d26ff768a79cdfc4c6eac67544f9dc80fd2902ba04db49e5463b4c9b73efefaa3d7ce4c8963e514894d5d4b00760baba04bed35fe1c7362523104ccff67bef0b755a482f8d2c2812f1b1ee3cb10511f4f83e645dd5963c78f460064e60a326dc2f850cc1d326d9694d4ce99b0f0929dc9b11c8be766168b4b3aad54ee9fbbc90bcddfe54fcac6b6cc97eeaf43b49ddd17957ba002f2e6e55a1060cc89948c4b23d0ceaa7052210f61bca27186efd57283f47ac149e05b75329e304423f44836c12fa401bbd5ea84e7b1f5cba33f29763a3b1a91991d8ca42b8f3ef1379decaa917dc854cd58884d22f92fdaa37873420b6b8d1a02c8810dc17fe26081b3896bed67fc7fa5729d3d1c0342eb36e7087a211636aca5faf7cd6d0550bc2102bf6a712edc9bbe278e87323f54132383b6bd07a1da98ec9dcef396dc31e941425acbcfc341a7e1a313f3bfc0168671ec6f790cb71a9be74053f6b01518c63cb8379070ac84a10e0f0116a5d4e665526a1f36ab615359b64e5c91bb4d5027cd64d949f8b93f837b5edd8a4cb8257e3f3313fb0c114ac0db7e3a0d2d320352ae2d041843311e3684e5a6c4e4dd21dbb71547d082fd92be477ddb4c0183b93105a0da75a5ba61e2fa9ba4c75338ff1d27dd045b55d399fc86c2237a3028a33d1efba6b3f29566282cc75c5ac3dfa61e2d0b802e538906da154fa172130ccbe2ea11ea903c6e0b332866728b6a67f9f671693720fd88bf80f9f6f31644beb4c7409461053743a6ccd27cf8ab8e5052d9e017fe6fe793b67a96480cb70cfbb6a8f1c73ae0fb48040117dd2bf14e8faaed6e58fdbf00fe36df559074d73cb52c62ae894025a7247426317ea1e1522f9729838b8997ee26210e047d7658c35e58f863381f229265c8b2f8db03b11333b67c3b0b3e1665080d2c0943bae79d107c63f8516933ff6c5d45b3881fff16afa9585f5d0b1d834766a7a2cb3e474cab7782d2b687941a8ae33f3133af0b741f30598dca4e9384bad8c0848c5031d4cc219db1051a10f0273cadd88f37bb772babf5f44556e3c07e8282e65a48ce52f19986df89424ce1cb6759af2c53ed9bf05f1f8b5aca8f12d2f10334a063ef5fc88a45ef1f0a75ae85d6a17bacf5a2f221b4cf51eb5f92af0ca2610c687f127cae994072b63bb9a638b7816c9c7c1055e7f5ccbbb1311681dd7c79191325cf566f164cbb5d20a03b4e7a43f82db50faa8cfa0c3c56b98f4c83e4b4f35d172124e7fd1501eaf127b1f7b1ba9a71c03c56efc3e764868ccac0c45ad8782faac9fcd4bedba8350526e4609f7de69b06722f3ec35a29b23041714c0879a3591afe52c548d8201cfd92a555944f26e33c9938eb808241cb0091af358b41f7fd1347e4d618e9f759b6f51f646c6b5dbb1a98e3a0e0df7b11861fa438ed6c2a52d527b0a651491bd2cb9e170f8d5d1086ac7dc893bf6548ef4fc739457aa5de09a77e9261e8862c816c2f69f6ccb578532c314f97eb66e1779cda7f22c1caa0b2a54ec8fd6588cd9edd06ef06ce0b0806e35a88e92bdb9abc65f61024a48e06c8266fd42837fbdf00ebf3b5ede43b6391bfffd9"),
                       ('jpeg2000', "0000000c6a5020200d0a870a00000014667479706a703220000000006a7032200000002d6a703268000000166968647200000020000000200003070700000000000f636f6c720100000000001000000d8b6a703263ff4fff51002f000000000020000000200000000000000000000000200000002000000000000000000003070101070101070101ff52000c00000001000504040001ff5c00134040484850484850484850484850484850ff640025000143726561746564206279204f70656e4a5045472076657273696f6e20322e332e30ff90000a000000000d040001ff93c7d4040977c1f20106c7d404049fc07c20c0f900c07c8040080107c03a0c010c0084070707c0f90140f900c03e1040057f0305c1f38483e70907d40a0d5baab30c1897bf0b2ccdf607c03a141f38487da0a003cf0e13572c01e2b616dfc1f38483e70907d40a0d6a9ce90c459c710ff00205bfc3ea1187d41d0fb44411e2c3e4379101f73b3459b6a61066ff7f07649d884d89d90068baf1b3327f143c7a1cb72bb9df9494fa4cd8b4aec09fc7da211f68943ed1300a1613b5a6ecf3266bc9eaa4aab16e2717f77070d476d1ec90c7455f4761dcf465f302db51faec9e1b5c1cc854f250334e36e95a9fc3ea108fb44a1f689012abc11315c3e36f7995c0c44a9f3a5917df22504861216db8faca9431194af1b32b16847435f00b2817291621b99fcd79e5cce3c7da7b1f69fc7e08a026d03038ccfa865709f8fa0ebea3622eaf4f68a3672f799b0c95f3f93d793feb3ec88a21c6faa1ad7d154b21e40d1788a2442808f0594ef8d945d2f5fd17f95dc4129d3aad41246afaff2b5b61dbcd75a8f85056654a1f8eb6276d776c82321ab42845d07fa64283529ca80c46189524f52f8dd6479ceabeb07916d90a1740e9c1455434770c78797532824a27bb3df6265724c4e34a5d1c7ef87b2810eebe19104476c5b1abc42d1f9c52e4ac8902cba5a676f57293bc7119de8d7f6f821b1edfc7da873f0448fc1240173329ccc8cc1e00bf57e27208b6c7d1143b43bd351840f54f08f51bdace2d423e66b6f24cf61fae9a247158f196c44b41eb2a8f9f1f960cd4f4bd7cbf4f2be8992c7f48a83e2c6f182eff5a602c57ce86daceec1bd379018825ec2264078e7dc7f7f6a496115619cde81b18a829e8df8a5b5e188a0e7f23c4fc728edcc78cf77ba2b5c0df967f302adc347b999d512564cebd7d89c66fc579a8dd05547a181e4be9079acb1d9aa0b160981da8d3c38f451fbdfc217689831681d206d039c4a36f7909fb1d11d7e978215cb03a9c0e3bc7da8b3f0449f9a580198f765dce94872bb3e08a4fc1c743931627796b4efc0012ae795767e9e08e6f4a4f16bca96d0581cb5e09f10e068ed53c26297d927cc57d03c38beb213b0ea513e82b4caf48ac318401d37f34e79411c323bbb89509dfe4b4e0aa036d87a46dff1e529788bc2048fc28907f04a1d85024d15a22e1fa3ecb1d4d5264f7d72f4fa7d51851074efb387f0760929f7134e14472776446154ac013368e3711f63d6392f856197dcc74af2cf37241e89a893c8a0e6704903c92f86f4f9a83fde7d961d1505efb7f589c06c46d06d1fb4b6cded97310dfcfc2fe9f8682cfceff0010e715ca18e9343f215b1b4f38cd8c23c020f122af4cc1b9d265644f425d9279a479e9cdea4eb33864945cca8bc7148026429e977a508a39bf44f0ea5e1ba474ad9131083f77af6394e471ff83e77c3465f8a37c98680fd9443662d3ded723aa65c3bf8f6f4fff045b1ef10e68b5f53b78ef6d863aded77d5ce9fc5db54b37b2a4e22bb8aefc776149ddd58b0292e9dccca564ac2cbe802b1ff5c6530c243fa50fa4043431f982604881dc430471d64a4a247d4cf58d10a1b8422509205df5a087468f25c6798329961a9ad22f1ed39782673c4c6ddd2f12276ee794063a73d8208c92708b37a5c00e64be8ee21c639511854f24636ea5d7896e6de25b81ab6e2ba7e3d494b2f1f6c812143a51c3bcd60e3665cab9316af52befe64f6040d0d6a3254aa6232d3e085260a1ff650110ca5e13ea208e46e1c18a0f1e8ecd702bb7400687b0b9a64b52b63ee8653fc2681eba192ec26449c155f4c0bc45340341f0552ffe49e9ff2743ee6b3c81c5e79d91e71af4b6e1be023879e6d294fe45e20a7b06a1c2c4d79b3974a9a02347d55a2bd6006c6eb5627af3105cbf106f1aaf75efb9d75f7102339b1f7e67929cfe7c94fcbff4b603b347cd61babe2af40ee461416152f1704152af09f0a2a32e6c21e43ad0eb8e3917d776687a80ac0ad691c6f45459d800ca65dc0cbe187fc0ad61d33a0d90404a6491ecb77a903d90f35135211934a060c11096eea69b989383ed43f71834dab91fda63a8dccf9b39a85d5df94a59b6a88bde98f95ca7a037a46023efb85e2230cd5d4ee126038cd43f26f4199532e48eaf6fb88a2ea710e9ac84c8631aa5ae3132c23efb223b77552b7fbac317b472744c1bea68f8e8963bf20a4341383a2eceff6186eac2bd07a6cd7ecbed28557288fdad0d2f72172ce71237166b9d1b6fc692bafce66ed62754850df9210de6b558eb5ed329ae1ae8c1d83c2a7abeeb4861593cb9aa60c3e685c41716c63ee9dcc197078446346440f1bd385df84935829bf5554afda187344c3c1f4d214479384651ea15c1eb08dfaf52941d61a39fc8755b35b8eea0f220467ab36b9c1fcfc2fa9f8687c7e1a1203625a30755cc1c5536012034f6376b5a5315f867c613c12ada7fb95bdb6b93f41a727b238d473c64060f59e99f81927422f7627504e02f34b17b2ca62fa85e5c17a87726d0a91996e5aeebc4224f26bdbdeaf35da463ebc009dc29ee8fb9d003b6282f515241df887c2a3df30ee0332ec78f672ca29a5f6893bb051b86763ae80214f2e1f3a1765380691d9836a8f8ab1e7c735fcc55a15d405f6eee202ec968f3c9bcc98cee2df70d509ab1e54578a79ef982fbfaeb5d2a6c1e060a1f5221c5ce7bf26bc00b5da7a1bcd34638dad21b0df045591f5090bd74fb2dff3b4e95b91091b573ddb5baa67ce3bd1dd0cd3330cea9ca65a0180633cdf31d2b721c22789aa7005af0db25e627bbb9b6662f2f54b3715cd1059f210d33a9711ce012596c3d7b47322a14577ffcdbd0ddf9a67729ba4665fd9e788b224dfabd912fde48c074d2326bdbc749018afbf777b9898a4e7c60901f2d288aa6e6a8b6073afd740cc98e50d9e8070f1afb0ca7657e17b653f8f3725e1f0b2a48f4572d6f589a11ea8aba88bbf7ec76ce923040aab560a78b61237ee74b17691e5690b45478229f9bfbca60f4928c6e255933e8c934fc68e4c8d087812b9fa4a63d0b44a124babc5d3646e6dc5eafb08452e359d369936a0c8eb75d26ff768a79cdfc4c6eac67544f9dc80fd2902ba04db49e5463b4c9b73efefaa3d7ce4c8963e514894d5d4b00760baba04bed35fe1c7362523104ccff67bef0b755a482f8d2c2812f1b1ee3cb10511f4f83e645dd5963c78f460064e60a326dc2f850cc1d326d9694d4ce99b0f0929dc9b11c8be766168b4b3aad54ee9fbbc90bcddfe54fcac6b6cc97eeaf43b49ddd17957ba002f2e6e55a1060cc89948c4b23d0ceaa7052210f61bca27186efd57283f47ac149e05b75329e304423f44836c12fa401bbd5ea84e7b1f5cba33f29763a3b1a91991d8ca42b8f3ef1379decaa917dc854cd58884d22f92fdaa37873420b6b8d1a02c8810dc17fe26081b3896bed67fc7fa5729d3d1c0342eb36e7087a211636aca5faf7cd6d0550bc2102bf6a712edc9bbe278e87323f54132383b6bd07a1da98ec9dcef396dc31e941425acbcfc341a7e1a313f3bfc0168671ec6f790cb71a9be74053f6b01518c63cb8379070ac84a10e0f0116a5d4e665526a1f36ab615359b64e5c91bb4d5027cd64d949f8b93f837b5edd8a4cb8257e3f3313fb0c114ac0db7e3a0d2d320352ae2d041843311e3684e5a6c4e4dd21dbb71547d082fd92be477ddb4c0183b93105a0da75a5ba61e2fa9ba4c75338ff1d27dd045b55d399fc86c2237a3028a33d1efba6b3f29566282cc75c5ac3dfa61e2d0b802e538906da154fa172130ccbe2ea11ea903c6e0b332866728b6a67f9f671693720fd88bf80f9f6f31644beb4c7409461053743a6ccd27cf8ab8e5052d9e017fe6fe793b67a96480cb70cfbb6a8f1c73ae0fb48040117dd2bf14e8faaed6e58fdbf00fe36df559074d73cb52c62ae894025a7247426317ea1e1522f9729838b8997ee26210e047d7658c35e58f863381f229265c8b2f8db03b11333b67c3b0b3e1665080d2c0943bae79d107c63f8516933ff6c5d45b3881fff16afa9585f5d0b1d834766a7a2cb3e474cab7782d2b687941a8ae33f3133af0b741f30598dca4e9384bad8c0848c5031d4cc219db1051a10f0273cadd88f37bb772babf5f44556e3c07e8282e65a48ce52f19986df89424ce1cb6759af2c53ed9bf05f1f8b5aca8f12d2f10334a063ef5fc88a45ef1f0a75ae85d6a17bacf5a2f221b4cf51eb5f92af0ca2610c687f127cae994072b63bb9a638b7816c9c7c1055e7f5ccbbb1311681dd7c79191325cf566f164cbb5d20a03b4e7a43f82db50faa8cfa0c3c56b98f4c83e4b4f35d172124e7fd1501eaf127b1f7b1ba9a71c03c56efc3e764868ccac0c45ad8782faac9fcd4bedba8350526e4609f7de69b06722f3ec35a29b23041714c0879a3591afe52c548d8201cfd92a555944f26e33c9938eb808241cb0091af358b41f7fd1347e4d618e9f759b6f51f646c6b5dbb1a98e3a0e0df7b11861fa438ed6c2a52d527b0a651491bd2cb9e170f8d5d1086ac7dc893bf6548ef4fc739457aa5de09a77e9261e8862c816c2f69f6ccb578532c314f97eb66e1779cda7f22c1caa0b2a54ec8fd6588cd9edd06ef06ce0b0806e35a88e92bdb9abc65f61024a48e06c8266fd42837fbdf00ebf3b5ede43b6391bfffd9"),
                       ):
        if encoding not in ENCODINGS:
            #removed already
            continue
        try:
            cdata = binascii.unhexlify(hexdata)
            buf = BytesIOClass(cdata)
            img = PIL.Image.open(buf)
            assert img, "failed to open image data"
            raw_data = img.tobytes("raw", img.mode)
            assert raw_data
            #now try with junk:
            cdata = binascii.unhexlify("ABCD"+hexdata)
            buf = BytesIOClass(cdata)
            try:
                img = PIL.Image.open(buf)
                log.warn("Pillow failed to generate an error parsing invalid input")
            except Exception as e:
                log("correctly raised exception for invalid input: %s", e)
        except Exception as e:
            try:
                #py2k:
                datainfo = cdata.encode("string_escape")
            except:
                try:
                    datainfo = cdata.encode("unicode_escape").decode()
                except:
                    datainfo = str(hexdata)
            log.warn("Pillow error decoding %s with data=%s..", encoding, datainfo[:16])
            log.warn(" %s", e, exc_info=True)
            ENCODINGS.remove(encoding)
