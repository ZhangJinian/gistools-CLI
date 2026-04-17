import click
from cli.convert import convert
from cli.reproject import reproject
from cli.buffer import buffer
from cli.analysis import analysis
from cli.spatial import spatial
from cli.data import data

@click.group()
def cli():
    """GISTools — GIS 操作命令行工具包"""
    pass

cli.add_command(convert)
cli.add_command(reproject)
cli.add_command(buffer)
cli.add_command(analysis)
cli.add_command(spatial)
cli.add_command(data)
