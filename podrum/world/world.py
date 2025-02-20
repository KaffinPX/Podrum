#########################################################
#  ____           _                                     #
# |  _ \ ___   __| |_ __ _   _ _ __ ___                 #
# | |_) / _ \ / _` | '__| | | | '_ ` _ \                #
# |  __/ (_) | (_| | |  | |_| | | | | | |               #
# |_|   \___/ \__,_|_|   \__,_|_| |_| |_|               #
#                                                       #
# Copyright 2021 Podrum Team.                           #
#                                                       #
# This file is licensed under the GPL v2.0 license.     #
# The license file is located in the root directory     #
# of the source code. If not you may not use this file. #
#                                                       #
#########################################################

from collections import deque
import math
from podrum.block.block_map import block_map
from podrum.geometry.vector_2 import vector_2
from podrum.task.immediate_task import immediate_task

class world:
    def __init__(self, provider: object, server: object):
        self.provider: object = provider
        self.server: object = server
        self.chunks: dict = {}
        self.mark_as_loading: object = deque()
        self.world_path: str = provider.world_dir
    
    # [load_chunk]
    # :return: = None
    # Loads a chunk.
    def load_chunk(self, x: int, z: int) -> None:
        if f"{x} {z}" not in self.mark_as_loading:
            self.mark_as_loading.append(f"{x} {z}")
            chunk: object = self.provider.get_chunk(x, z)
            if chunk is None:
                generator: object = self.server.managers.generator_manager.get_generator(self.get_generator_name())
                chunk: object = generator.generate(x, z, self)
            self.chunks[f"{x} {z}"] = chunk
            self.mark_as_loading.remove(f"{x} {z}")
    
    # [load_radius]
    # :return: = None
    # Loads a radius.
    def load_radius(self, x: int, z: int, radius: int) -> None:
        tasks: list = []
        chunk_x_start: int = (math.floor(x) >> 4) - radius
        chunk_x_end: int = (math.floor(x) >> 4) + radius
        chunk_z_start: int = (math.floor(z) >> 4) - radius
        chunk_z_end: int = (math.floor(z) >> 4) + radius
        for chunk_x in range(chunk_x_start, chunk_x_end):
            for chunk_z in range(chunk_z_start, chunk_z_end):
                if not self.has_loaded_chunk(chunk_x, chunk_z):
                    chunk_task: object = immediate_task(self.load_chunk, [chunk_x, chunk_z])
                    chunk_task.start()
                    tasks.append(chunk_task)
        for task in tasks:
            task.join()
    
    # [send_radius]
    # :return: = None
    # Sends a radius to a player.
    def send_radius(self, x: int, z: int, radius: int, player: object) -> None:
        self.load_radius(x, z, radius)
        tasks: list = []
        chunk_x_start: int = (math.floor(x) >> 4) - radius
        chunk_x_end: int = (math.floor(x) >> 4) + radius
        chunk_z_start: int = (math.floor(z) >> 4) - radius
        chunk_z_end: int = (math.floor(z) >> 4) + radius
        for chunk_x in range(chunk_x_start, chunk_x_end):
            for chunk_z in range(chunk_z_start, chunk_z_end):
                if self.has_loaded_chunk(chunk_x, chunk_z):
                    chunk: object = self.get_chunk(chunk_x, chunk_z)
                    send_task: object = immediate_task(player.send_chunk, [chunk])
                    send_task.start()
                    tasks.append(send_task)
        for task in tasks:
            task.join()
        player.send_network_chunk_publisher_update()
    
    # [unload_chunk]
    # :return: = None
    # Unloads a chunk.
    def unload_chunk(self, x: int, z: int) -> None:
        self.provider.save_chunk(x, z)
        del self.chunks[f"{x} {z}"]

    # [has_loaded_chunk]
    # :return: = bool
    # Checks if a chunk is loaded.
    def has_loaded_chunk(self, x: int, z: int) -> bool:
        if f"{x} {z}" in self.chunks:
            return True
        return False
    
    # [get_chunk]
    # :return: = object
    # Gets a chunk.
    def get_chunk(self, x: int, z: int) -> object:
        return self.chunks[f"{x} {z}"]
        
    # [save_chunk]
    # :return: = None
    # Saves a chunk to its file.
    def save_chunk(self, x: int, z: int) -> None:
        self.provider.set_chunk(self.get_chunk(x, z))
    
    # [get_block]
    # :return: = None
    # Gets a block.
    def get_block(self, x: int, y: int, z: int, block: object) -> None:
        block_and_meta: tuple = block_map.get_name_and_meta(self.chunks[f"{x >> 4} {z >> 4}"].get_block_runtime_id(x & 0x0f, y & 0x0f, z & 0x0f))
        return self.server.managers.block_manager.get_block(block_and_meta[0], block_and_meta[1])
    
    # [set_block]
    # :return: = None
    # Sets a block.
    def set_block(self, x: int, y: int, z: int, block: object) -> None:
        self.chunks[f"{x >> 4} {z >> 4}"].set_block_runtime_id(x & 0x0f, y & 0x0f, z & 0x0f, block.runtime_id)
        
    # [get_highest_block_at]
    # :return: = int
    # Get the highest block y position.
    def get_highest_block_at(self, x: int, z: int) -> int:
        return self.chunks[f"{x >> 4} {z >> 4}"].get_highest_block_at(x & 0x0f, z & 0x0f)
    
    # [save]
    # :return: = None
    # idk here lol
    def save(self) -> None:
        tasks: list = []
        for chunk in self.chunks.values():
            chunk_task: object = immediate_task(self.save_chunk, [chunk.x, chunk.z])
            chunk_task.start()
            tasks.append(chunk_task)
        for task in tasks:
            task.join()
    
    # [get_world_name]
    # :return: = str
    # Gets a world name.
    def get_world_name(self) -> str:
        return self.provider.get_world_name()
    
    # [set_world_name]
    # :return: = None
    # Sets a world name.
    def set_world_name(self, world_name: str) -> None:
        self.provider.set_world_name(world_name)
        
    # [get_spawn_position]
    # :return: = object
    # Gets the world spawn position.
    def get_spawn_position(self) -> object:
        return self.provider.get_spawn_position()
    
    # [set_spawn_position]
    # :return: = None
    # Sets a spawn position.
    def set_spawn_position(self, world_name: object) -> None:
        self.provider.set_spawn_position(world_name)

    # [get_world_gamemode]
    # :return: = None
    # Gets the world's default generator.
    def get_world_gamemode(self) -> str:
        return self.provider.get_world_gamemode()
        
    # [set_world_gamemode]
    # :return: = None
    # Sets the default world gamemode.
    def set_world_gamemode(self, world_name: str) -> None:
        self.provider.set_world_gamemode(world_name)
        
    # [get_player_position]
    # :return: = object
    # Gets a vector_3 that contains a player's
    # current position.
    def get_player_position(self, uuid: str) -> object:
        return self.provider.get_player_position(uuid)
        
    # [set_player_position]
    # :return: = None
    # Sets a player's default position.
    def set_player_position(self, uuid: str, position: object) -> None:
        self.provider.set_player_position(uuid, position)

    # [get_player_gamemode]
    # :return: = int
    # Gets player gamemode.
    def get_player_gamemode(self, uuid: str) -> int:
        return self.provider.get_player_gamemode(uuid)
        
    # [set_player_gamemode]
    # :return: = None
    # Sets a player's gamemode.
    def set_player_gamemode(self, uuid: str, gamemode: int) -> None:
        self.provider.set_player_gamemode(uuid, gamemode)
        
    # [create_player]
    # :return: = None
    # Creates a new player file.
    def create_player(self, uuid: str) -> None:
        self.provider.create_player_file(uuid)
        
    # [has_player]
    # :return: = bool
    # Checks if a player exists.
    def has_player(self, uuid: str) -> bool:
        return self.provider.has_player_file(uuid)
        
    # [get_generator_name]
    # :return: = None
    # Gets the default generator name.
    def get_generator_name(self) -> str:
        return self.provider.get_generator_name()
    
    # [set_generator_name]
    # :return: = None
    # Sets the default generator name.
    def set_generator_name(self, generator_name: str) -> None:
        self.provider.set_generator_name(generator_name)