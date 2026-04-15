import click
from cli.convert import convert

@click.group()
def cli():
    """GISTools — GIS 操作命令行工具包"""
    pass

cli.add_command(convert)
