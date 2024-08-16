from spikeinterface.core import BaseRecording, BaseRecordingSegment
from spikeinterface.core.core_tools import define_function_from_class
from pyns import nsparser
import glob
import numpy as np


class RippleRecordingExtractor(BaseRecording):
    extractor_name = 'Ripple'
    has_default_locations = False
    mode = 'file'
    name = 'ripple'

    def __init__(self):
        ns5files = list(glob.glob('*.ns5'))
        if not ns5files:
            error("No ripple file sound")
        fname = ns5files[0]
        parser = nsparser.ParserFactory(fname)
        sampling_frequency = parser.timestamp_resolution
        if parser.bytes_per_point == 2:
            if not parser.is_float:
                dtype = np.int16
            else:
                dtype = np.float16
        # get the channel labels
        channel_ids = [ee.electrode_label.decode('utf-8').strip('\x00') for ee in parser.get_extended_headers()]
        BaseRecording.__init__(self, channel_ids=channel_ids, sampling_frequency=sampling_frequency, dtype=dtype)
        recording_segment = RippleRecordingSegment(parser, sampling_frequency, dtype)
        self.add_recording_segment(recording_segment)

    def is_binary_compatible(self):
        return True

    def get_binary_description(self):
        return {"time_axis" : 0,
                "dtype" : self.dtype,
                "num_channels" : self.get_num_channels()}


class RippleRecordingSegment(BaseRecordingSegment):
    def __init__(self, parser, sampling_frequency, dtype):
        BaseRecordingSegment.__init__(self, sampling_frequency = sampling_frequency)
        self.parser = parser 
        self.dtype = dtype
        self.num_channels = parser.channel_count

    def get_num_samples(self):
        return self.parser.n_data_points

    def get_traces(self, start_frame, end_frame, channel_indices):
        if type(channel_indices) == slice:
            start = 0 if channel_indices.start == None else channel_indices.start
            stop = 1 if channel_indices.stop == None else channel_indices.stop
            step = 1 if channel_indices.step == None else channel_indices.step
            chs = range(start,stop,step)
            nch = stop - start
        elif channel_indices is None:
            chs = range(self.num_channels) 
            nchs = self.num_channels
        else:
            chs = channel_indices
            nch = len(channel_indices)
        buffer = np.zeros((end_frame-start_frame,nch), dtype=self.dtype) 
        for i,ch in enumerate(chs):
            buffer[:,i] = self.parser.get_analog_data(ch, start_frame, buffer.shape[0])
        return buffer

read_ripple_recording = define_function_from_class(source_class=RippleRecordingExtractor, name="read_ripple_recording")
