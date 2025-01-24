import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots


import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class Plot:
    def __init__(self):
        pass
        # self.rebar = Rebar()

    def xi_coordinate(self, spans):
        numS = 1000
        Xt = [np.linspace(0, span, numS) for span in spans]
        return numS, Xt

    def x_coordinate(self, spans, stretch, Xt):
        X = []
        temp = 0
        for i, span in enumerate(spans):
            if i > 0:
                temp += stretch[i - 1].L
            X += (Xt[i] + temp).tolist()
        return X

    def plot_curve(
        self,
        label,
        spans,
        Ltotal,
        stretch,
        DFQ,
        max_values,
        min_values,
        Xmax_values,
        Xmin_values,
    ):
        numS, Xt = self.xi_coordinate(spans)
        X = self.x_coordinate(spans, stretch, Xt)

        invert_y = label != "Shear"
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=X, y=DFQ, mode="lines"))

        if invert_y:
            fig.update_yaxes(autorange="reversed")

        if max_values is not None:
            self._add_markers(
                fig,
                spans,
                Ltotal,
                stretch,
                max_values,
                min_values,
                Xmax_values,
                Xmin_values,
            )

        Xgraf = [0] + X + [Ltotal]
        DFQgraf = [0] + DFQ + [0]
        fig.add_trace(
            go.Scatter(
                x=Xgraf,
                y=DFQgraf,
                fill="tozeroy",
                fillcolor="rgba(0, 0, 255, 0.3)",
                mode="none",
            )
        )

        return fig

    def _add_markers(
        self,
        fig,
        spans,
        Ltotal,
        stretch,
        max_values,
        min_values,
        Xmax_values,
        Xmin_values,
    ):
        temp = 0
        for i, span in enumerate(spans):
            if i > 0:
                temp += stretch[i - 1].L
            ubicMax = temp + Xmax_values[i]
            ubicMin = temp + Xmin_values[i]
            ubicMax = Ltotal - stretch[i].L / 2 if ubicMax == Ltotal else ubicMax
            ubicMin = Ltotal - stretch[i].L / 2 if ubicMin == Ltotal else ubicMin

            fig.add_trace(
                go.Scatter(
                    x=[ubicMax],
                    y=[max_values[i] / 1000],
                    mode="markers",
                    text=[str(round(max_values[i] / 1000, 2))],
                    textposition="top center",
                    marker=dict(color="red", size=10),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=[ubicMin],
                    y=[min_values[i] / 1000],
                    mode="markers",
                    text=[str(round(min_values[i] / 1000, 2))],
                    textposition="bottom center",
                    marker=dict(color="blue", size=10),
                )
            )

    def plot_curves(
        self,
        spans,
        Ltotal,
        stretch,
        shearDFQ,
        momentDFQ,
        maxShear,
        minShear,
        XmaxQ,
        XminQ,
        maxMoment,
        minMoment,
        XmaxM,
        XminM,
        deflectionDFQ=None,
    ):
        shear_fig = self.plot_curve(
            "Shear", spans, Ltotal, stretch, shearDFQ, maxShear, minShear, XmaxQ, XminQ
        )
        moment_fig = self.plot_curve(
            "Moment",
            spans,
            Ltotal,
            stretch,
            momentDFQ,
            maxMoment,
            minMoment,
            XmaxM,
            XminM,
        )
        if deflectionDFQ != None:
            deflection_fig = self.plot_curve(
                "Deflection",
                spans,
                Ltotal,
                stretch,
                deflectionDFQ,
                None,
                None,
                None,
                None,
            )

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(
                "Shear Force Diagram(kN)",
                "Bending Moment Diagram(kN-m)",
                "Delta by Cubic Interpolation",
            ),
        )

        for trace in shear_fig["data"]:
            fig.add_trace(trace, row=1, col=1)
        for trace in moment_fig["data"]:
            fig.add_trace(trace, row=2, col=1)
        if deflectionDFQ != None:
            for trace in deflection_fig["data"]:
                fig.add_trace(trace, row=3, col=1)

        fig.update_yaxes(visible=False, row=3, col=1)
        fig.update_layout(height=800, showlegend=False)

        return fig
