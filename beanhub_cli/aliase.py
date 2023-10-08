import click

from beanhub_cli.context import Context


class AliasedGroup(click.Group):
    def get_command(self, ctx: Context, cmd_name: str):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.logger.error(f"Too many matches: %s", ", ".join(sorted(matches)))

    def resolve_command(self, ctx: Context, args: list[str]):
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args
