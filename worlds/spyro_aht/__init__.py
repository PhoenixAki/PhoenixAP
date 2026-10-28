import Utils
import asyncio

from .AHTWorld import SpyroAHTWorld
from worlds.LauncherComponents import Component, components, icon_paths
icon_paths['spyro_aht'] = f'ap:{__name__}/icons/dark_gem_icon.png'

def _run_client(*args: str):
    import colorama
    from CommonClient import server_loop, gui_enabled, get_base_parser
    Utils.init_logging("Spyro_AHT")

    async def _main(connect: str | None, password: str | None):
        from .client.context import SpyroAHTContext, tracker_loaded
        ctx = SpyroAHTContext(connect, password)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
        if tracker_loaded:
            ctx.run_generator()
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        await asyncio.sleep(1)

        await ctx.exit_event.wait()
        ctx.watcher_event.set()
        ctx.server_address = None
        await ctx.shutdown()
    
    parser = get_base_parser()
    parsed_args = parser.parse_args(args)
    colorama.init()
    asyncio.run(_main(parsed_args.connect, parsed_args.password))
    colorama.deinit()

def run_client():
    from multiprocessing import Process
    Process(target=_run_client, name="SpyroAHTClient").start()

components.append(Component("Spyro AHT Client", func=run_client, icon='spyro_aht'))
