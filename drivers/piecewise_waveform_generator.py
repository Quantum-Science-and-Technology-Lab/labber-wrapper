from math import floor
from dataclasses import dataclass
from typing import Optional
import VISA_Driver from VISA_Driver


@dataclass
class Piece(object):
    volts: float
    time_ns: float
    ramp_time_ns: Optional[float] = None
    length: Optional[int] = None

    def __len__(self):
        return self.length


class Piecewise(object):

    def __init__(self, pieces, ramp_time_ns, repeat=1, resolution_ns=1):
        for i, piece in enumerate(pieces):
            assert isinstance(piece, Piece)
            if piece.time_ns < 2 * resolution_ns:
                print(f'WARNING: piecewise function segment of length {piece.time_ns}ns depends on sampling beyond the Nyquist frequency.')
            if piece.ramp_time_ns is None and i != 0:
                piece.ramp_time_ns = ramp_time_ns
            elif piece.ramp_time_ns is None and repeat == 1 and i == 0:
                piece.ramp_time_ns = 0
            elif piece.ramp_time_ns is None and repeat != 1 and i == 0:
                piece.ramp_time_ns = ramp_time_ns
            if piece.length is None:
                piece.length = floor((piece.time_ns + piece.ramp_time_ns) / resolution_ns)

        self._pieces = pieces
        self._ramp_time = ramp_time_ns
        self._piece_index = 0
        self._raster_index = 0
        self._repeat_index = 0
        self._repeat = repeat
        self.resolution = resolution_ns

        waveform_length = 0
        for i, piece in enumerate(pieces):
            if i != len(pieces) - 1:
                waveform_length += floor((piece.time_ns + piece.ramp_time_ns) / resolution_ns)
            else:
                waveform_length += floor(piece.time_ns / resolution_ns)

        self.length = waveform_length

    def add(self, piece):
        assert isinstance(piece, Piece)
        if piece.ramp_time_ns is None:
            piece.ramp_time_ns = self._ramp_time
        self._pieces.append(piece)

    def insert(self, piece, index):
        assert isinstance(piece, Piece)
        before = self._pieces[0:index]
        after = self._pieces[index:]
        self._pieces = before + [piece] + after

    def remove(self, index):
        del self._pieces[index]

    def __len__(self):
        return self.length * self._repeat

    def __iter__(self):
        return self

    def __next__(self):

        # conditionally move to next piece
        if self._piece_index < len(self._pieces) - 1 and self._raster_index == len(self._pieces[self._piece_index]):
            self._piece_index += 1
            self._raster_index = 0

        # conditionally repeat the waveform from the start
        elif self._repeat_index < self._repeat - 1 and self._raster_index == len(self._pieces[self._piece_index]) \
                and self._piece_index == len(self._pieces) - 1:
            self._repeat_index += 1
            self._piece_index = 0
            self._raster_index = 0

        # end the iteration when we finish the last piece
        elif self._repeat_index == self._repeat - 1 and self._piece_index == len(self._pieces) - 1 \
            and self._raster_index == len(self._pieces[self._piece_index]):
            self._piece_index = 0
            self._raster_index = 0
            self._repeat_index = 0
            raise StopIteration

        # get the current piece
        piece = self._pieces[self._piece_index]

        # skip the ramp on the first piece of the first iteration
        if self._repeat_index == 0 and self._piece_index == 0 and self._raster_index == 0:
            self._raster_index += floor(piece.ramp_time_ns / self.resolution)

        # raster the ramp between pieces
        if self._raster_index < floor(piece.ramp_time_ns / self.resolution):
            curr_raster = self._raster_index
            self._raster_index += 1

            # get the starting voltage
            if self._piece_index != 0:
                target = self._pieces[self._piece_index - 1].volts
            elif self._repeat_index != 0:
                target = self._pieces[len(self._pieces) - 1].volts

            # calculate the slope
            slope = (piece.volts - target) / floor(piece.ramp_time_ns / self.resolution)
            x = curr_raster

            # get the voltage at this instant
            y = slope * x + target
            return y

        # raster the piece
        elif self._raster_index < floor((piece.time_ns + piece.ramp_time_ns) / self.resolution):
            self._raster_index += 1
            return piece.volts


class AWGPiecewiseWaveformDriver(VISA_Driver):

    def performOpen(self, options={}):
        """Perform the open instrument connection operation"""
        self.dMeasParam = {}
        VISA_Driver.performOpen(self, options=options)

    def performClose(self, bError=False, options={}):
        """Perform the close instrument connection operation"""
        pass

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        return value

    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""

        # we write one driver per signal / experiment?? Or pass params to options?
        if quant.name == 'Signal':
            signal = Piecewise(
                pieces=[
                    Piece(volts=1, time_ns=10),
                    Piece(volts=2, time_ns=10),
                    Piece(volts=1, time_ns=10)
                ],
                ramp_time_ns=3,
                resolution_ns=1
            )
            trace = quant.getTraceDict(signal, t0=0.0, dt=1)  # return the trace object
            return trace
        else:
            # for other quantities, just return current value of control
            return quant.getValue()
