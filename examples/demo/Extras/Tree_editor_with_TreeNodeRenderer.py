# -----------------------------------------------------------------------------
# Copyright (c) 2019, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# -----------------------------------------------------------------------------
"""
This demo illustrates use of TreeNodeRenderers for displaying more complex
contents inside the cells of a TreeEditor.
"""

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

from random import choice, uniform
import colorsys

import numpy as np

from pyface.qt import QtCore, QtGui
from traits.api import Array, Float, HasTraits, Instance, Int, List, RGBColor, Unicode

from traitsui.api import TreeEditor, TreeNode, UItem, View
from traitsui.tree_node_renderer import AbstractTreeNodeRenderer
from traitsui.qt4.tree_editor import WordWrapRenderer


class MyDataElement(HasTraits):
    #: Some text to display.
    text = Unicode

    #: A random walk to plot.
    data = Array

    #: A color to show as an icon.
    color = RGBColor

    def _data_default(self):
        return np.random.standard_normal((1000,)).cumsum()

    def _color_default(self):
        return colorsys.hsv_to_rgb(uniform(0.0, 1.0), 1.0, 1.0)


class MyData(HasTraits):
    #: The name of the root node.
    name = Unicode('Rooty McRootface')

    #: The elements contained in the root node.
    elements = List(Instance(MyDataElement))

    def _elements_default(self):
        DATA_ELEMENTS = (
            'I live on\nmultiple\nlines!',
            'Foo\nBar',
            'Baz',
            'Qux',
            'z ' * 20,
            __doc__,
        )
        return [MyDataElement(text=choice(DATA_ELEMENTS)) for _ in range(5)]


class SparklineRenderer(AbstractTreeNodeRenderer):
    """ Renderer that draws sparklines into a cell. """

    #: This renderer handles all rendering.
    handles_all = True

    #: This renderer handles text rendering (there is none).
    handles_text = True

    #: The scale for y-values.
    y_scale = Float(1.0)

    #: The extra border applied by Qt internally
    # XXX get this dynamically from Qt? How?
    extra_space = Int(8)

    def paint(self, editor, node, column, object, paint_context):
        painter, option, index = paint_context
        data = self.get_data(object)

        xs = np.linspace(0, option.rect.width(), len(data)) + option.rect.left()
        ys = (data.max() - data)/self.y_scale + option.rect.top()

        height = option.rect.height()
        plot_height = ys.ptp()
        extra = height - plot_height
        if bool(option.displayAlignment & QtCore.Qt.AlignVCenter):
            ys += extra/2
        elif bool(option.displayAlignment & QtCore.Qt.Bottom):
            ys += extra

        if bool(option.state & QtGui.QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())

        points = [QtCore.QPointF(x, y) for x, y in zip(xs, ys)]
        old_pen = painter.pen()
        if bool(option.state & QtGui.QStyle.State_Selected):
            painter.setPen(QtGui.QPen(option.palette.highlightedText(), 0))
        try:
            painter.drawPolyline(points)
        finally:
            painter.setPen(old_pen)

        return None

    def get_data(self, object):
        return object.data

    def size(self, editor, node, column, object, size_context):
        data = self.get_data(object)
        return (100, data.ptp()/self.y_scale + self.extra_space)


class SparklineTreeNode(TreeNode):
    """ A TreeNode that renders sparklines in column index 1 """

    # static instances of renderers( they have no state, so this is fine)
    sparkline_renderer = SparklineRenderer()
    word_wrap_renderer = WordWrapRenderer()

    def get_renderer(self, object, column=0):
        if column == 1:
            return self.sparkline_renderer
        else:
            return self.word_wrap_renderer

    def get_icon(self, object, is_expanded):
        return object.color


class SparklineTreeView(HasTraits):
    """ Class that views the data with sparklines. """

    #: The root of the tree.
    root = Instance(MyData, args=())

    traits_view = View(
        UItem(
            'root',
            editor=TreeEditor(
                nodes=[
                    TreeNode(
                        node_for=[MyData],
                        children='elements',
                        label='name',
                    ),
                    SparklineTreeNode(
                        node_for=[MyDataElement],
                        auto_open=True,
                        label='text',
                    ),
                ],
                column_headers=["The Tree View", "The Sparklines"],
                hide_root=False,
                editable=False,
            ),
        ),
        resizable=True,
        width=400,
        height=300,
    )


if __name__ == '__main__':
    SparklineTreeView().configure_traits()
