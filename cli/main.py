import click
from cli.convert import convert
from cli.reproject import reproject

@click.group()
def cli():
    """GISTools — GIS 操作命令行工具包"""
    pass

cli.add_command(convert)
cli.add_command(reproject)
