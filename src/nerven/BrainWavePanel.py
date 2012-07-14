import wx, scipy, scipy.fftpack
from collections import deque
import numpy as np
from nerven_panels import *
from consts import *
from epoc.epoc_bits import TAIL_LEN

class BrainWavePanel(NervenPlotPanel):
    def init_plot(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.plot = SensorPlot(self, SENSOR_PLOT_ID)
        self.wave_tail = {}
        self.plotted_axes = {}
        self.draw_counter = 1001
        self.normalize = False
        maxlen = TAIL_LEN*SAMPLE_FREQ
        for wave in BRAIN_WAVES:
            self.wave_tail[wave] = deque([0.0]*maxlen, maxlen=maxlen)
        hsizer0 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.norm_cb = wx.CheckBox(self, -1, 'Normalize power')
        self.Bind(wx.EVT_CHECKBOX, self.on_norm, self.norm_cb)
        hsizer0.Add(self.norm_cb)
        self.sizer.Add(hsizer0)
        self.sizer.Add(self.plot, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        
    def do_update(self):
        draw = True
        if self.draw_counter < PLOT_UPDATE_FREQ:
            self.draw_counter += 1
            draw = False

        fig = self.plot.get_figure()
        axes = fig.gca()
        wave_power = dict([(k,0.0) for k,v in BRAIN_WAVES.items()])
        for i, sensor in enumerate(self.epoc.sensors):
            vals = np.array(self.epoc.sensor_tail[sensor], dtype='float')
            sensor_waves = self.extract_waves(vals)
            for k,v in sensor_waves.items():
                wave_power[k] += v
        for wave in wave_power:
            wave_power[wave] /= len(self.epoc.sensors)
            self.wave_tail[wave].append(wave_power[wave])
        if draw:
            self.draw_counter = 0
            x = np.arange(0.0, TAIL_LEN, (1.0/SAMPLE_FREQ))
            for wave in BRAIN_WAVES:
                axes.plot(x, self.wave_tail[wave], label=wave)
            if self.normalize:
                axes.set_ylim(0.0, 1.0)
            axes.legend()
            self.plot.draw()
            fig.delaxes(axes)

    def extract_waves(self, vals):
        wave_power = dict([(k,0.0) for k,v in BRAIN_WAVES.items()])
        dft = abs(np.fft.fft(vals))
        for wave in wave_power:
            lower, upper = BRAIN_WAVES[wave]
            wave_power[wave] = self.get_bin(lower, upper, dft)
        if self.normalize:
            total_power = sum(wave_power.values())
            for wave in wave_power:
                wave_power[wave] /= total_power
        return wave_power
            
    def get_bin(self, lower, upper, dft_vals):
        a = int(lower/SAMPLE_FREQ*len(dft_vals))
        b = int(upper/SAMPLE_FREQ*len(dft_vals))
        return sum(dft_vals[a:b])

    def on_norm(self, e):
        self.normalize = self.norm_cb.GetValue()
        
        
