##########################################################################
# CAPSUL - Copyright (C) CEA, 2015
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from soma.qt_gui.qt_backend import QtCore, QtGui
try:
    import traits.api as traits
except ImportError:
    import enthought.traits.api as traits


class PipelineFileWarningWidget(QtGui.QSplitter):
    """
    This class is a GUI for pipeline file inputs/outputs checking.

    It allows to check if there are missing inputs which may prevent the
    pipeline from running, or if there are already existing outputs which would
    be overwritten if the pipeline runs.

    It will show warnings accordingly.

    The widget is built from the output of
    :py:func:`capsul.pipeline_tools.nodes_with_missing_inputs` and
    :py:func:`capsul.pipeline_tools.nodes_with_existing_outputs`
    """

    def __init__(self, missing_inputs, overwritten_outputs, parent=None):
        super(PipelineFileWarningWidget, self).__init__(
            QtCore.Qt.Vertical, parent)
        """
        Builds the check widget.

        Parameters
        ----------
        missing_inputs: mapping iterable (mandatory)
            a dict node: (list of pairs (param_name, file_name))
            as output of
            :py:func:`capsul.pipeline_tools.nodes_with_missing_inputs`
        overwritten_outputs: mapping iterable (mandatory)
            a dict node: (list of pairs (param_name, file_name))
            as output of
            :py:func:`capsul.pipeline_tools.nodes_with_existing_outputs`
        parent: QWidget (optional)
            parent widget
        """
        splitter = self
        widget1 = QtGui.QWidget(splitter)
        layout1 = QtGui.QVBoxLayout(widget1)
        widget2 = QtGui.QWidget(splitter)
        layout2 = QtGui.QVBoxLayout(widget2)
        label = QtGui.QLabel()
        layout1.addWidget(label)

        text = '<h1>Pipeline file parameters problems</h1>\n'

        if len(missing_inputs) == 0:
            text += '<h2>Inputs: OK</h2>\n' \
                '<p>All input file are present.</p>\n'
            label.setText(text)
        else:
            text += '<h2>Inputs: missing files</h2>\n'
            label.setText(text)

            table = QtGui.QTableWidget()
            layout1.addWidget(table)
            table.setColumnCount(3)
            sizes = [len(l) for node, l in missing_inputs.iteritems()]
            table.setRowCount(sum(sizes))
            table.setHorizontalHeaderLabels(
                ['node', 'parameter', 'filename'])
            row = 0
            for node_name, items in missing_inputs.iteritems():
                for param_name, file_name in items:
                    if not file_name or file_name is traits.Undefined:
                        file_name = '<temp. file>'
                    table.setItem(row, 0, QtGui.QTableWidgetItem(node_name))
                    table.setItem(row, 1,
                                  QtGui.QTableWidgetItem(param_name))
                    table.setItem(row, 2, QtGui.QTableWidgetItem(file_name))
                    row += 1
            table.setSortingEnabled(True)
            table.resizeColumnsToContents()

        label_out = QtGui.QLabel()
        layout2.addWidget(label_out)
        if len(overwritten_outputs) == 0:
            text = '<h2>Outputs: OK</h2>\n' \
                '<p>No output file will be overwritten.</p>\n'
            label_out.setText(text)
        else:
            text = '<h2>Outputs: overwritten files</h2>\n'
            label_out.setText(text)

            table = QtGui.QTableWidget()
            layout2.addWidget(table)
            table.setColumnCount(3)
            sizes = [len(l) for node, l in overwritten_outputs.iteritems()]
            table.setRowCount(sum(sizes))
            table.setHorizontalHeaderLabels(
                ['node', 'parameter', 'filename'])
            row = 0
            for node_name, items in overwritten_outputs.iteritems():
                for param_name, file_name in items:
                    if not file_name or file_name is traits.Undefined:
                        file_name = '<temp. file>'
                    table.setItem(row, 0, QtGui.QTableWidgetItem(node_name))
                    table.setItem(row, 1,
                                  QtGui.QTableWidgetItem(param_name))
                    table.setItem(row, 2, QtGui.QTableWidgetItem(file_name))
                    row += 1
            table.setSortingEnabled(True)
            table.resizeColumnsToContents()
