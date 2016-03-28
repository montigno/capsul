##########################################################################
# CAPSUL - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

from __future__ import absolute_import

import xml.etree.cElementTree as ET

from soma.sorted_dictionary import OrderedDict

from capsul.process.xml import string_to_value
from capsul.pipeline.pipeline_construction import PipelineConstructor


def create_xml_pipeline(module, name, xml_file):
    """
    Create a pipeline class given its Capsul XML 2.0 representation.
    
    Parameters
    ----------
    module: str (mandatory)
        name of the module for the created Pipeline class (the Python module is
        not modified).
    name: str (mandatory)
        name of the new pipeline class
    xml_file: str (mandatory)
        name of file containing the XML description.
    
    """
    xml_pipeline = ET.parse(xml_file).getroot()
    version = xml_pipeline.get('capsul_xml')
    if version and version != '2.0':
        raise ValueError('Only Capsul XML 2.0 is supported, not %s' % version)

    builder = PipelineConstructor(module, name)
    exported_parameters = set()
    
    for child in xml_pipeline:
        if child.tag == 'doc':
            builder.set_documentation(child.text.strip())
        elif child.tag == 'process':
            process_name = child.get('name')
            module = child.get('module')
            args = (process_name, module)
            kwargs = {}
            nipype_usedefault = []
            iterate = []
            for process_child in child:
                if process_child.tag == 'set':
                    name = process_child.get('name')
                    value = process_child.get('value')
                    value = string_to_value(value)
                    if value is not None:
                        kwargs[name] = value
                    kwargs.setdefault('make_optional', []).append(name)
                elif process_child.tag == 'iterate':
                    name = process_child.get('name')
                    iterate.append(name)
                elif process_child.tag == 'nipype':
                    name = process_child.get('name')
                    usedefault = process_child.get('usedefault')
                    if usedefault == 'true':
                        nipype_usedefault.append(name)
                    copyfile = process_child.get('copyfile')
                    if copyfile == 'true':
                        kwargs.setdefault('inputs_to_copy', []).append(name)
                    elif copyfile == 'discard':
                        kwargs.setdefault('inputs_to_copy', []).append(name)
                        kwargs.setdefault('inputs_to_clean', []).append(name)
                else:
                    raise ValueError('Invalid tag in <process>: %s' %
                                     process_child.tag)
            if iterate:
                kwargs['iterative_plugs'] = iterate
                builder.add_iterative_process(*args, **kwargs)
            else:
                builder.add_process(*args, **kwargs)
            for name in nipype_usedefault:
                builder.call_process_method(process_name, 'set_usedefault',
                                            name, True)
        elif child.tag == 'link':
            source = child.get('source')
            dest = child.get('dest')
            if '.' in source:
                if '.' in dest:
                    builder.add_link('%s->%s' % (source, dest))
                elif dest in exported_parameters:
                    builder.add_link('%s->%s' % (source, dest))
                else:
                    node, plug = source.rsplit('.', 1)
                    builder.export_parameter(node, plug, dest)
                    exported_parameters.add(dest)
            elif source in exported_parameters:
                builder.add_link('%s->%s' % (source, dest))
            else:
                node, plug = dest.rsplit('.', 1)
                builder.export_parameter(node, plug, source)
                exported_parameters.add(source)
        elif child.tag == 'processes_selection':
            selection_parameter = child.get('name')
            selection_groups = OrderedDict()
            for select_child in child:
                if select_child.tag == 'processes_group':
                    group_name = select_child.get('name')
                    group = selection_groups[group_name] = []
                    for group_child in select_child:
                        if group_child.tag == 'process':
                            group.append(group_child.get('name'))
                        else:
                            raise ValueError('Invalid tag in <processes_group>'
                                             '<process>: %s' % group_child.tag)
                else:
                    raise ValueError('Invalid tag in <processes_selection>: %s'
                                     % select_child.tag)
            builder.add_processes_selection(selection_parameter,
                                            selection_groups)
        elif child.tag == 'gui':
            for gui_child in child:
                if gui_child.tag == 'position':
                    name = gui_child.get('name')
                    x = float(gui_child.get('x'))
                    y = float(gui_child.get('y'))
                    builder.set_node_position(name, x, y)
                elif gui_child.tag == 'zoom':
                    builder.set_scene_scale_factor(
                        float(gui_child.get('level')))
                else:
                    raise ValueError('Invalid tag in <gui>: %s' %
                                     gui_child.tag)
        else:
            raise ValueError('Invalid tag in <pipeline>: %s' % child.tag)
    return builder.pipeline


def save_xml_pipeline(pipeline, xml_file):
    '''
    Save a pipeline in an XML file

    Parameters
    ----------
    pipeline: Pipeline instance
        pipeline to save
    xml_file: str
        XML file to save the pipeline in
    '''
    # imports are done locally to avoid circular imports
    from capsul.api import Process, Pipeline
    from capsul.pipeline.pipeline_nodes import ProcessNode, Switch
    from capsul.pipeline.process_iteration import ProcessIteration
    from capsul.process.process import NipypeProcess

    def _write_process(process, parent, name):
        procnode = ET.SubElement(parent, 'process')
        mod = process.__module__
        # if process is a function with XML decorator, we need to
        # retreive the original function name.
        func = getattr(process, '_function', None)
        if func:
            classname = func.__name__
        else:
            classname = process.__class__.__name__
        procnode.set('module', "%s.%s" % (mod, classname))
        procnode.set('name', name)
        if isinstance(process, NipypeProcess):
            # WARNING: not sure I'm doing the right things for nipype. To be
            # fixed if needed.
            for param in process.inputs_to_copy:
                elem = ET.SubElement(procnode, 'nipype')
                elem.set('name', param)
                if param in proces.inputs_to_clean:
                    elem.set('copyfile', 'discard')
                else:
                    elem.set('copyfile', 'true')
                np_input = getattr(process._nipype_interface.inputs, param)
                if np_input:
                    use_default = getattr(np_input, 'usedefault', False) # is it that?
                    if use_default:
                        elem.set('use_default', 'true')
            for param, np_input in \
                    process._nipype_interface.inputs.__dict__.iteritems():
                use_default = getattr(np_input, 'usedefault', False) # is it that?
                if use_default and param not in process.inputs_to_copy:
                    elem = ET.SubElement(procnode, 'nipype')
                    elem.set('name', param)
                    elem.set('use_default', 'true')
        return procnode

    def _write_iteration(process_iter, parent, name):
        procnode = _write_process(process_iter.process, parent, name)
        for param in process_iter.iterative_parameters:
            elem = ET.SubElement(procnode, 'iterate')
            elem.set('name', param)

    def _write_processes(pipeline, root):
        proc_dict = pipeline_dict.setdefault("processes", OrderedDict())
        for node_name, node in pipeline.nodes.iteritems():
            if node_name == "":
                continue
            if isinstance(node, Switch):
                switch = ET.SubElement(root, 'switch')
                #switch_descr = _switch_description(node)
            elif isinstance(node, ProcessNode) \
                    and isinstance(node.process, ProcessIteration):
                _write_iteration(node.process, root, node_name)
            else:
                _write_process(node.process, root, node_name)

    def _write_links(pipeline, root):
        for node_name, node in pipeline.nodes.iteritems():
            for plug_name, plug in node.plugs.iteritems():
                if (node_name == "" and not plug.output) \
                        or (node_name != "" and plug.output):
                    links = plug.links_to
                    for link in links:
                        if node_name == "":
                            src = plug_name
                        else:
                            src = "%s.%s" % (node_name, plug_name)
                        if link[0] == "":
                            dst = link[1]
                        else:
                            dst = "%s.%s" % (link[0], link[1])
                        linkelem = ET.SubElement(root, 'link')
                        linkelem.set('source', src)
                        linkelem.set('dest', dst)
                        if link[-1]:
                            linkelem.set('weak', 1)

    def _write_nodes_positions(pipeline, root):
        gui = None
        if hasattr(pipeline, "node_position") and pipeline.node_position:
            gui = ET.SubElement(root, 'gui')
            for node_name, pos in pipeline.node_position.iteritems():
                node_pos = ET.SubElement(gui, 'position')
                node_pos.set('name', node_name)
                node_pos.set('x', unicode(pos[0]))
                node_pos.set('y', unicode(pos[1]))
        return gui

    root = ET.Element('pipeline')
    class_name = pipeline.__class__.__name__
    if pipeline.__class__ is Pipeline:
        # if directly a Pipeline, then use a default new name
        class_name = 'CustomPipeline'
    root.set('name', class_name)
    pipeline_dict = OrderedDict([("@class_name", class_name)])
    xml_dict = OrderedDict([("pipeline", pipeline_dict)])

    if hasattr(pipeline, "__doc__"):
        docstr = pipeline.__doc__
        if docstr == Pipeline.__doc__:
            docstr = ""  # don't use the builtin Pipeline help
        else:
            # remove automatically added doc
            autodocpos = docstr.find(
                ".. note::\n\n    * Type '{0}.help()'".format(
                    pipeline.__class__.__name__))
            if autodocpos >= 0:
                docstr = docstr[:autodocpos]
    else:
        docstr = ""
    root.set('doc', docstr)
    _write_processes(pipeline, root)
    _write_links(pipeline, root)
    gui_node = _write_nodes_positions(pipeline, root)

    if hasattr(pipeline, "scene_scale_factor"):
        if gui_node is None:
            gui_node = ET.SubElement(root, 'gui')
        scale_node = ET.SubElement(gui_node, 'zoom')
        scale_node.set('level', unicode(pipeline.scene_scale_factor))

    tree = ET.ElementTree(root)
    tree.write(xml_file)

