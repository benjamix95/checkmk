#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
"""Folders

Folders are used in Checkmk to organize the hosts in a tree structure.
The root (or main) folder is always existing, other folders can be created manually.
If you build the tree cleverly you can use it to pass on attributes in a meaningful manner.

You can find an introduction to hosts including folders in the
[Checkmk guide](https://docs.checkmk.com/latest/en/wato_hosts.html).
"""
from typing import List

from cmk.gui import watolib
from cmk.gui.exceptions import MKUserError
from cmk.gui.http import Response
from cmk.gui.plugins.openapi import fields
from cmk.gui.plugins.openapi.endpoints.host_config import host_collection
from cmk.gui.plugins.openapi.restful_objects import (
    constructors,
    Endpoint,
    request_schemas,
    response_schemas,
)
from cmk.gui.plugins.openapi.utils import ProblemException
from cmk.gui.watolib import CREFolder

# TODO: Remove all hard-coded response creation in favour of a generic one
# TODO: Implement formal description (GET endpoint) of move action

FOLDER_FIELD = {
    'folder': fields.FolderField(
        example='~my~fine~folder',
        required=True,
    )
}


@Endpoint(constructors.collection_href('folder_config'),
          'cmk/create',
          method='post',
          etag='output',
          response_schema=response_schemas.ConcreteFolder,
          request_schema=request_schemas.CreateFolder)
def create(params):
    """Create a folder"""
    put_body = params['body']
    name = put_body['name']
    title = put_body['title']
    parent_folder = put_body['parent']
    attributes = put_body.get('attributes', {})

    if parent_folder.has_subfolder(name):
        raise ProblemException(status=400,
                               title="Path already exists",
                               detail=f"The path '{parent_folder.name()}/{name}' already exists.")

    folder = parent_folder.create_subfolder(name, title, attributes)

    return _serve_folder(folder)


@Endpoint(
    constructors.domain_object_collection_href('folder_config', '{folder}', 'hosts'),
    '.../collection',
    method='get',
    path_params=[FOLDER_FIELD],
    response_schema=response_schemas.DomainObjectCollection,
)
def hosts_of_folder(params):
    """Show all hosts in a folder
    """
    folder = params['folder']
    return host_collection(folder.hosts())


@Endpoint(constructors.object_href('folder_config', '{folder}'),
          '.../persist',
          method='put',
          path_params=[FOLDER_FIELD],
          etag='both',
          response_schema=response_schemas.ConcreteFolder,
          request_schema=request_schemas.UpdateFolder)
def update(params):
    """Update a folder
    """
    folder = params['folder']
    constructors.require_etag(constructors.etag_of_obj(folder))

    post_body = params['body']
    title = post_body['title']
    replace_attributes = post_body['attributes']
    update_attributes = post_body['update_attributes']
    remove_attributes = post_body['remove_attributes']

    attributes = folder.attributes().copy()

    if replace_attributes:
        attributes = replace_attributes

    if update_attributes:
        attributes.update(update_attributes)

    for attribute in remove_attributes:
        folder.remove_attribute(attribute)

    folder.edit(title, attributes)

    return _serve_folder(folder)


@Endpoint(constructors.domain_type_action_href('folder_config', 'bulk-update'),
          'cmk/bulk_update',
          method='put',
          response_schema=response_schemas.FolderCollection,
          request_schema=request_schemas.BulkUpdateFolder)
def bulk_update(params):
    """Bulk update folders"""
    body = params['body']
    entries = body['entries']
    folders = []

    for update_details in entries:
        folder = update_details['folder']
        title = update_details['title']
        replace_attributes = update_details['attributes']
        update_attributes = update_details['update_attributes']
        remove_attributes = update_attributes['remove_attributes']
        attributes = folder.attributes().copy()

        if replace_attributes:
            attributes = replace_attributes

        if update_attributes:
            attributes.update(update_attributes)

        for attribute in remove_attributes:
            folder.remove_attribute(attribute)

        folder.edit(title, attributes)
        folders.append(folder)

    return constructors.serve_json(_folders_collection(folders, False))


@Endpoint(constructors.object_href('folder_config', '{folder}'),
          '.../delete',
          method='delete',
          path_params=[FOLDER_FIELD],
          output_empty=True)
def delete(params):
    """Delete a folder"""
    folder = params['folder']
    parent = folder.parent()
    parent.delete_subfolder(folder.name())
    return Response(status=204)


@Endpoint(constructors.object_action_href('folder_config', '{folder}', action_name='move'),
          'cmk/move',
          method='post',
          path_params=[FOLDER_FIELD],
          response_schema=response_schemas.ConcreteFolder,
          request_schema=request_schemas.MoveFolder,
          etag='both')
def move(params):
    """Move a folder"""
    folder: watolib.CREFolder = params['folder']
    folder_id = folder.id()

    constructors.require_etag(constructors.etag_of_obj(folder))

    dest_folder: watolib.CREFolder = params['body']['destination']

    try:
        folder.parent().move_subfolder_to(folder, dest_folder)
    except MKUserError as exc:
        raise ProblemException(
            title="Problem moving folder.",
            detail=exc.message,
            status=400,
        )
    folder = fields.FolderField.load_folder(folder_id)
    return _serve_folder(folder)


@Endpoint(
    constructors.collection_href('folder_config'),
    '.../collection',
    method='get',
    query_params=[{
        'show_hosts': fields.Boolean(
            description=("When set, all hosts that are stored in each folder will also be shown. "
                         "On large setups this may come at a performance cost, so by default this "
                         "is switched off."),
            example=False,
            missing=False,
        )
    }],
    response_schema=response_schemas.FolderCollection)
def list_folders(params):
    """Show all folders"""
    folders = watolib.Folder.root_folder().subfolders()
    return constructors.serve_json(_folders_collection(folders, params['show_hosts']))


def _folders_collection(
    folders: List[CREFolder],
    show_hosts: bool,
):
    folders_ = []
    for folder in folders:
        if show_hosts:
            folders_.append(
                constructors.domain_object(
                    domain_type='folder_config',
                    identifier=folder.id(),
                    title=folder.title(),
                    extensions={
                        'attributes': folder.attributes().copy(),
                    },
                    members={
                        'hosts': constructors.object_collection(
                            name='hosts',
                            domain_type='folder_config',
                            entries=[
                                constructors.collection_item("host_config", {
                                    "title": host,
                                    "id": host
                                }) for host in folder.hosts()
                            ],
                            base="",
                        )
                    },
                ))
        folders_.append(
            constructors.collection_item(
                domain_type='folder_config',
                obj={
                    'title': folder.title(),
                    'id': folder.id()
                },
            ))
    collection_object = constructors.collection_object(
        domain_type='folder_config',
        value=folders_,
        links=[constructors.link_rel('self', constructors.collection_href('folder_config'))],
    )
    return collection_object


@Endpoint(
    constructors.object_href('folder_config', '{folder}'),
    'cmk/show',
    method='get',
    response_schema=response_schemas.ConcreteFolder,
    etag='output',
    query_params=[{
        'show_hosts': fields.Boolean(
            description=("When set, all hosts that are stored in this folder will also be shown. "
                         "On large setups this may come at a performance cost, so by default this "
                         "is switched off."),
            example=False,
            missing=False,
        )
    }],
    path_params=[FOLDER_FIELD],
)
def show_folder(params):
    """Show a folder"""
    folder = params['folder']
    return _serve_folder(folder, show_hosts=params['show_hosts'])


def _serve_folder(
    folder,
    profile=None,
    show_hosts=False,
):
    folder_json = _serialize_folder(folder, show_hosts)
    response = constructors.serve_json(folder_json, profile=profile)
    response.headers.add("ETag", constructors.etag_of_obj(folder).to_header())
    return response


def _serialize_folder(folder: CREFolder, show_hosts):
    uri = constructors.object_href('folder_config', folder.id())
    rv = constructors.domain_object(
        domain_type='folder_config',
        identifier=folder.id(),
        title=folder.title(),
        members={
            'move': constructors.object_action(
                name='move',
                base=uri,
                parameters=dict([
                    constructors.action_parameter(
                        action='move',
                        parameter='destination',
                        friendly_name='The destination folder of this move action',
                        optional=False,
                        pattern="[0-9a-fA-F]{32}|root",
                    ),
                ]),
            ),
        },
        extensions={
            'attributes': folder.attributes().copy(),
        },
    )
    if show_hosts:
        rv['members']['hosts'] = constructors.collection_property(
            name='hosts',
            base=constructors.object_href(
                'folder_config',
                "~" + folder.path().replace("/", "~"),
            ),
            value=[
                constructors.collection_item(
                    domain_type='host_config',
                    obj={
                        'title': host.name(),
                        'id': host.id()
                    },
                ) for host in folder.hosts()
            ],
        )
    return rv
