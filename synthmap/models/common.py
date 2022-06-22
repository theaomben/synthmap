from typing import NewType, Union

import numpy as np
from pydantic import HttpUrl, FileUrl, constr, BaseModel as PyBaseModel

IPFSURI = NewType("IPFSURI", constr(regex=r"^ipfs://.+"))
S3URI = NewType("S3URI", constr(regex=r"^s3://.+"))
GenericURL = NewType("GenericURL", Union[HttpUrl, FileUrl, IPFSURI, S3URI])
GenericURI = NewType("GenericURI", Union[HttpUrl, IPFSURI])
MD5Hex = Union[constr(regex=r"^[A-F0-9]{32}$"), constr(regex=r"^[a-f0-9]{32}$")]


class BaseModel(PyBaseModel):
    def is_eq(self, other):
        sd = dict(self)
        od = dict(other)
        for key, value in sd.items():
            if not key in od:
                return False
            if isinstance(value, np.ndarray):
                if not (value == od[key]).all():
                    return False
            elif isinstance(value, BaseModel):
                if not value.is_eq(od[key]):
                    return False
            elif isinstance(value, dict):
                for idx, item in value.items():
                    if not item.is_eq(od[key][idx]):
                        return False
            elif not value == od[key]:
                return False
        return True
