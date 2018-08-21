from capsul.process.process import Process
from capsul.process.nipype_process import NipypeProcess
from capsul.pipeline.pipeline import Pipeline
from capsul.pipeline.pipeline_nodes import Plug
from capsul.pipeline.pipeline_nodes import Node
from capsul.pipeline.pipeline_nodes import ProcessNode
from capsul.pipeline.pipeline_nodes import PipelineNode
from capsul.pipeline.pipeline_nodes import Switch
from capsul.pipeline.pipeline_nodes import OptionalOutputSwitch
from capsul.process.instance import get_process_instance
from capsul.study_config.study_config import StudyConfig
from capsul.utils.finder import find_processes
