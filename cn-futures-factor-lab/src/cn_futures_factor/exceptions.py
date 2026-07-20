"""项目自定义异常。

使用明确的异常类型，比直接抛出 ``ValueError`` 更容易在命令行、Notebook 和未来的
Web 服务中分别处理错误，也能避免把真正的程序缺陷误报成“数据有问题”。
"""


class FuturesFactorError(Exception):
    """所有可预期业务异常的基类。"""


class ConfigurationError(FuturesFactorError):
    """配置文件缺失、格式错误或参数不合理。"""


class DataValidationError(FuturesFactorError):
    """输入数据违反标准数据契约。"""


class InsufficientDataError(FuturesFactorError):
    """有效样本不足，无法继续构造因子或组合。"""
