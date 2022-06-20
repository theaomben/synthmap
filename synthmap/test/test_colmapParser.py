# pylint: disable=R0201
import importlib.resources
import os

import numpy as np
import pytest

from synthmap.projectManager import colmapParser

TEST_ROOT = importlib.resources.files("synthmap.test")


@pytest.fixture
def sample_array_blobs():
    return [
        [
            np.array(
                [[6, 227], [209, 98], [49, 179], [17, 177], [96, 183]], dtype=np.uint8
            ),
            b"\x06\xe3\xd1b1\xb3\x11\xb1`\xb7",
        ],
        [
            np.array(
                [
                    [-0.641124, 0.37178183, 0.77535343],
                    [0.8507359, -0.14382243, -0.9473336],
                    [0.65217733, 0.73200893, 0.7311528],
                ],
                dtype=np.float32,
            ),
            b"\xb4 $\xbf0Z\xbe>\x90}F?\xd4\xc9Y?0F\x13\xbet\x84r\xbf\x18\xf5&?\xf0d;?\xd4,;?",
        ],
        [
            np.array(
                [
                    [
                        6.18068275e-01,
                        7.45376852e-01,
                        6.52354080e-02,
                        6.28944831e-01,
                        8.35920388e-01,
                        8.35223542e-02,
                        9.07196731e-01,
                        2.32685718e-01,
                        5.86252559e-01,
                        9.23468044e-01,
                        4.95798298e-01,
                        3.34946184e-01,
                        7.39541084e-01,
                        9.10207104e-01,
                        7.97645088e-01,
                        5.42699280e-01,
                        1.76003646e-01,
                        4.90728430e-01,
                        6.94964395e-03,
                        1.34764986e-01,
                        3.68927050e-01,
                        8.45483666e-01,
                        6.27537126e-01,
                        8.84646251e-01,
                        2.27164922e-01,
                        2.78129832e-02,
                        5.46325210e-01,
                        5.94382153e-01,
                        6.70506753e-01,
                        4.86837317e-01,
                        3.21472896e-01,
                        2.68093367e-01,
                    ],
                    [
                        7.31062014e-01,
                        8.95740926e-01,
                        7.67231301e-01,
                        1.83635758e-01,
                        3.21683351e-02,
                        7.85318841e-01,
                        9.89908768e-01,
                        2.22860237e-01,
                        2.86798100e-01,
                        4.18621814e-01,
                        3.93114533e-01,
                        8.37237256e-01,
                        1.22693853e-01,
                        8.54088655e-01,
                        7.20225001e-01,
                        2.38165489e-01,
                        4.38856366e-01,
                        1.31815067e-01,
                        5.64579856e-01,
                        8.99134503e-01,
                        9.66694149e-01,
                        3.38154999e-01,
                        7.83872993e-01,
                        8.67371077e-01,
                        6.03378533e-02,
                        2.81295399e-01,
                        8.86319259e-01,
                        2.75670278e-02,
                        6.57147142e-01,
                        5.00928682e-01,
                        6.38826282e-01,
                        3.68501740e-01,
                    ],
                    [
                        8.91943805e-01,
                        1.00795850e-01,
                        1.01330075e-01,
                        2.79549403e-02,
                        8.02708288e-01,
                        2.88273241e-01,
                        3.96694260e-01,
                        7.58111345e-01,
                        5.13002509e-01,
                        8.88581819e-02,
                        5.81763139e-01,
                        3.90141624e-01,
                        9.65208865e-01,
                        8.74723500e-02,
                        8.81034707e-01,
                        6.11881080e-01,
                        9.73824959e-01,
                        8.25557290e-01,
                        3.82582628e-01,
                        9.38476458e-01,
                        3.27749105e-01,
                        5.56254390e-01,
                        9.76966946e-02,
                        5.55677079e-02,
                        4.90765706e-01,
                        7.30917084e-01,
                        6.13554283e-01,
                        2.02943668e-01,
                        2.78214112e-01,
                        9.33334458e-01,
                        8.93203807e-04,
                        6.61898308e-01,
                    ],
                    [
                        6.27595853e-02,
                        4.79585540e-01,
                        8.95856146e-01,
                        4.68721205e-01,
                        4.23711938e-01,
                        3.68305132e-01,
                        3.54102426e-01,
                        2.08168773e-01,
                        1.85400037e-02,
                        8.27320524e-01,
                        3.51850426e-02,
                        7.35200243e-01,
                        5.91648450e-01,
                        3.46910868e-01,
                        5.32178844e-01,
                        7.56931176e-01,
                        2.81305276e-01,
                        4.67694760e-02,
                        3.80271021e-01,
                        3.74159884e-01,
                        2.29321677e-01,
                        8.40850349e-01,
                        4.34767147e-01,
                        3.50450499e-01,
                        4.89481677e-01,
                        5.71965937e-01,
                        2.46625503e-01,
                        3.27172294e-01,
                        6.99292559e-02,
                        7.44524019e-02,
                        1.07080600e-02,
                        4.53603648e-01,
                    ],
                    [
                        6.12468779e-01,
                        6.90663764e-01,
                        4.76001962e-01,
                        4.18709995e-01,
                        6.28925415e-01,
                        3.13140817e-01,
                        5.04721979e-01,
                        4.68622272e-01,
                        2.23142494e-01,
                        6.43043941e-01,
                        2.86466805e-01,
                        1.70075193e-02,
                        1.98430646e-01,
                        6.56817345e-01,
                        3.44843574e-01,
                        4.10982515e-01,
                        2.07198368e-01,
                        7.59027216e-01,
                        7.42335381e-02,
                        9.21884854e-01,
                        5.86354482e-01,
                        3.81566312e-01,
                        4.64873355e-01,
                        3.48426648e-01,
                        7.72935574e-01,
                        9.90208561e-02,
                        8.30189876e-01,
                        4.40979173e-01,
                        7.54928157e-03,
                        6.77092569e-01,
                        5.09474263e-01,
                        7.27446325e-01,
                    ],
                ],
                dtype=np.float64,
            ),
            b"\x8a>z\x1e7\xc7\xe3?C\"Q\x8e \xda\xe7?$\xb6\xe6\x87D\xb3\xb0?\x8fC\x04\xe9P \xe4?\xd1\xa0\x10\x1d\xdc\xbf\xea?) \xc6\x93\xb8a\xb5?\x08\xdcUp\xc1\x07\xed?#4\x87F\xa5\xc8\xcd?\xef=\x03\xba\x94\xc2\xe2?\xe21\xfc\xda\x0c\x8d\xed?9\xa3\xd4\xc8(\xbb\xdf?\xc6\xcc\x8c\x1e\xc2o\xd5?)\x82:\x10R\xaa\xe7?5\x8a\x08\xa6j \xed?%\xcd\xd8\xfdN\x86\xe9?95e\xe1\xca]\xe1?F\xfc\xc5\x97I\x87\xc6?\xb2P\x847\x18h\xdf?\x9f\xd9\xbe\xd7:w|?\xf1\x08\xc2\xa3\xfa?\xc1?A\x06\x973\x80\x9c\xd7?\xc2\xb5\xd8\xc23\x0e\xeb?@D&\xbd\xc8\x14\xe4?E^\x92\xa7\x05O\xec?\xfe\xe9d{\xbd\x13\xcd?w'\xfe\xb4\x01{\x9c?H\xc5\xbd\x01\x7f{\xe1?\x12\xc1\x8e\xb8-\x05\xe3?\x92:\xfc\x93\xcat\xe5?P1\xbf\xb4W(\xdf?\xc9\xb4\xb7\r\x03\x93\xd4?\x97\x87\xe2\x14q(\xd1?\xe9J/*\xdcd\xe7?\xeez\xdb\xdf\xe8\xa9\xec?\xaafH\xa8(\x8d\xe8?\xd5:~c`\x81\xc7?(Jq6^x\xa0?L\xe2`\xfaT!\xe9?F\xad\x12'U\xad\xef?#5\xbf*\xaf\x86\xcc?\x19\x84\x03k\xe6Z\xd2?\xa4k!&\xb3\xca\xda?\xdaN\xb4\xdb\xc9(\xd9?\xb1h0\xc9\xa5\xca\xea?\xa7#\x0eF\xddh\xbf?\x10\x82#\xbb\xb1T\xeb?f\xcf!M\x15\x0c\xe7?\x80:%\xed4|\xce?H!\xe7\x029\x16\xdc?HI\xf1\xecP\xdf\xc0?1\x030\xc6\t\x11\xe2?\x08\xe3\xa2\xb8\xb5\xc5\xec?\xcd\x10f\x91(\xef\xee?:\xc5k\xddT\xa4\xd5?g\xe2\xa4\xd0|\x15\xe9?\xf4\xc2&\xfd\x80\xc1\xeb?\xf5\xc8De\x9a\xe4\xae?\xec\x18\xcej\xbe\x00\xd2?\xdc\t\xe74\xba\\\xec?\x07Le\xeb\x87:\x9c?\x85\x98qqY\x07\xe5?30Z\x96\x9b\x07\xe0?\x1f}\xa0\xd0Cq\xe4?\x0eltR\x88\x95\xd7?\x9d\x08\x0b\xbc\xcd\x8a\xec?\xc7\x90R\xbf\xc1\xcd\xb9?\x07\xea9\x8e\xc4\xf0\xb9?\x1e\x89fI8\xa0\x9c?R\x05\xa6J\xc9\xaf\xe9?\x15\x0b\x9a\x9b\x11s\xd2?\xbb\x7fMRpc\xd9?\xe3\x0c0\xb9rB\xe8?cx\xdd<\x84j\xe0?\xbc\x15>\xe9h\xbf\xb6?\xe4\xbe\x00\xbb\xcd\x9d\xe2?a\xda\xf8\x92\x14\xf8\xd8?7\x7f\x9f\xb3\xfd\xe2\xee?Z\xe4\x8d\x82\x96d\xb6?\x14\x97\xa6\xb2o1\xec?a\x84t\xa1\x87\x94\xe3?\x91\xdf\xdd\xf5\x92)\xef?\xc9\xc70\x1f\xf7j\xea?d\xc6\xd1\xd8;|\xd8?\x1e\xa1\xe5\xc7\xff\x07\xee?V+\xd1a\xd7\xf9\xd4?E\xce\xa9\x01\xd6\xcc\xe1?\x12\xfb;\x8c\xa6\x02\xb9?\x12\xd2I\xe0^s\xac?\xaa,Q\x90\xb4h\xdf?\x13\xc4{9\xacc\xe7?\x88\xc8y\x97<\xa2\xe3?\x8d\xc1~\xe0\x0e\xfa\xc9?\xf6\xd7\x14\x90B\xce\xd1?X\xe0\xaa9\xe0\xdd\xed?\xde\x98\xe2\x91\xbcDM?ThD\\E.\xe5?\xee\xbf_\x1e\x03\x11\xb0?\xd8\xce{\x8c\x87\xb1\xde?\x01\xb3\x1f\x82\xda\xaa\xec?g\xab\x9a9\x87\xff\xdd?;\xa0(\xad\x18\x1e\xdb?\xc5\xe48\xb0O\x92\xd7?3\xac\xc68\x9d\xa9\xd6?k\xae\n<F\xa5\xca?\xe7\xa3<\x96&\xfc\x92?ww<\xe4hy\xea?\xe1\xfc\x8c\x1e\xc6\x03\xa2?\xb4G\xf6\xa8\xc2\x86\xe7?\xb7T\xef\xba\xc8\xee\xe2?]\xf7+\xa4\xc93\xd6?{LS\xed\x9b\x07\xe1?/\xc5\xc7\xba\xc78\xe8?*/'\xd8\xe7\x00\xd2?+\xfb\xbd3+\xf2\xa7?\x18\xf0\xb3C\\V\xd8?pTPL<\xf2\xd7?\xcaK}\xa7iZ\xcd?? \xb9\xfd>\xe8\xea?\xd7_o\x959\xd3\xdb?\xb2\x99\x04\xee\xc7m\xd6?\xf62\xad\xf4\xaaS\xdf?q\xe9:\x82\x8bM\xe2?iM\xdf\xaal\x91\xcf?y\xc9\xb8\x0fd\xf0\xd4?\x01\xc6\x1f;\xe2\xe6\xb1?\xe7\xe6D\x07P\x0f\xb3?ub\x07|\x1b\xee\x85?'g`\x98\xd7\x07\xdd?\x9d\x08\xf4\x1fX\x99\xe3?@1\xdd\xe4\xea\x19\xe6?$\xcc\xe7\xee\xd0v\xde?\xf9!\xc2\x01%\xcc\xda?\x15\x8b!1( \xe4?\xb3\xb1\x03\xc8\x7f\n\xd4?\xa7\x13,\xb5\xae&\xe0?\xad\xb3\x1aE\xe8\xfd\xdd?\xd9\xf7\t\xe9\xee\x8f\xcc?\xee\x8c\x0f\xe3\xd0\x93\xe4?\xc2U\xb7\xddxU\xd2?!\xe6\xb7Lkj\x91?6\r\x8c\xe7,f\xc9?\xbd\x0e\x07\xcf\xa5\x04\xe5?X5$\xc8\xea\x11\xd6?\xf5\xc7I\x9b\x89M\xda?\xf7\x1a,\xe3y\x85\xca?B\xce\xafq\xf3I\xe8?\x18\xe7g\x1a\xf8\x00\xb3?\x90rS\xaa\x14\x80\xed?X\xb2\x81yj\xc3\xe2?\xba\xe6\xd2\x1b\x95k\xd8?ao ,|\xc0\xdd?\xfc\xc0\x8dH\x9fL\xd6?\xf1\xd6\x87b\xe3\xbb\xe8?\xb8H\x92JnY\xb9?M}\xdc[\xea\x90\xea?\xd6\"\x90\xb5\x009\xdc?\xf4\x1e9\xd7\xfe\xeb~?(\x07\x07\t\xbe\xaa\xe5?t\xa37\xf8\x9cM\xe0?i\r\xef\x83=G\xe7?",
        ],
    ]


class TestConversions:
    def test_to_blobs(self, sample_array_blobs):
        for a, b in sample_array_blobs:
            assert colmapParser.array_to_blob(a) == b

    def test_blob_roundtrip(self, sample_array_blobs):
        for a, b in sample_array_blobs:
            assert np.all(
                np.equal(
                    colmapParser.blob_to_array(
                        colmapParser.array_to_blob(a), dtype=a.dtype, shape=a.shape
                    ),
                    a,
                )
            )


@pytest.fixture
def known_projects():
    # TODO: redundant with test.conftest.sample_project_data
    project_path = TEST_ROOT / "sample_data" / "project.ini"
    db_path = TEST_ROOT / "sample_data" / "big_images.db"
    image_path = TEST_ROOT / "sample_data" / "sample_big_images"
    colmapParser.update_project_paths(
        project_path, database_path=db_path, image_path=image_path
    )
    return [
        [
            project_path,
            {
                "project_type": "colmap",
                "project_file": project_path,
                "db_path": str(db_path),
                "image_path": str(image_path),
            },
        ]
    ]


class TestEnumeration:
    def test_get_proj_dirs(self, known_projects):
        for sample_proj_path, known_data in known_projects:
            assert colmapParser.get_proj_dirs(sample_proj_path) == known_data
