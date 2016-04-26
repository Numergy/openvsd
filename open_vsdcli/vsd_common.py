
from prettytable import PrettyTable
import click
from vsd_client import VSDConnection

def print_object(obj, only=None, exclude=[]):
    def _format_multiple_values(values):
        """Format list in string to be printable as prettytable"""
        row_value = ""
        if len(values) > 0:
            last = values.pop()
            for o in values:
                row_value += "%s\n" % o
            row_value += last
        return row_value


    def _print_table(obj, exclude):
        table = PrettyTable(["Field", "Value"])
        table.align["Field"] = "l"

        for key in obj.keys():
            if key not in exclude:
                if type(obj[key]) is list:
                    table.add_row([key, _format_multiple_values(obj[key])])
                else:
                    table.add_row([key, obj[key]])
        print table

    if only:
        if only in obj:
            print obj[only] 
        else:
            print "No such key : %s" %only
    else:
        _print_table(obj, exclude)


def check_id(**ids):
    # Remove '_id' at the end of key names
    new_ids = {}
    for k, v in ids.items():
        k = '_'.join(k.split('_')[0:-1])
        new_ids[k] = v
    ids = new_ids

    # Check one and only one id is specified
    nb_ids = 0
    for k, v in ids.items():
        if v is not None:
            nb_ids += 1
            good_k = k
    if nb_ids != 1:
        raise click.exceptions.UsageError(
            "You must specify only one id in %s" % ids.keys())

    return good_k, ids[good_k]


def netmask_to_length(netmask):
    tableSubnet={
        '0'   : 0,
        '128' : 1,
        '192' : 2,
        '224' : 3,
        '240' : 4,
        '248' : 5,
        '252' : 6,
        '254' : 7,
        '255' : 8,
    }
    netmask_splited = str(netmask).split('.')
    length = tableSubnet[ netmask_splited[0] ] + tableSubnet[ netmask_splited[1] ] + \
                tableSubnet[ netmask_splited[2] ] + tableSubnet[ netmask_splited[3] ]
    return str(length)


@click.group()
@click.option('--vsd-url', metavar='<url>', envvar='VSD_URL',
              help='VSD url http(s)://hostname:port/nuage/api_v1_0 (Env: VSD_URL)', required=True)
@click.option('--vsd-username',metavar='<username>', envvar='VSD_USERNAME',
              help='VSD Authentication username (Env: VSD_USERNAME)', required=True )
@click.option('--vsd-password',metavar='<password>', envvar='VSD_PASSWORD',
              help='VSD Authentication password (Env: VSD_PASSWORD)', required=True )
@click.option('--vsd-organization',metavar='<organization>', envvar='VSD_ORGANIZATION',
              help='VSD Authentication organization (Env: VSD_ORGANIZATION)', required=True )
@click.option('--show-only',metavar='<key>',
              help='Show only the value for a given key (usable for show and create command)' )
@click.option('--debug', is_flag=True, help='Active debug for request and response')
@click.option('--force-auth', is_flag=True, help='Do not use existing APIkey. Replay authentication')
@click.pass_context
def vsdcli(ctx, vsd_username, vsd_password, vsd_organization, vsd_url, show_only, debug, force_auth):
    """Command-line interface to the VSD APIs"""
    nc = VSDConnection(
            vsd_username,
            vsd_password,
            vsd_organization,
            vsd_url,
            debug=debug,
            force_auth=force_auth
         )
    ctx.obj['nc'] = nc
    ctx.obj['show_only'] = show_only


@vsdcli.command(name='me-show')
@click.option('--verbose', count=True, help='Show APIKey')
@click.pass_context
def me_show(ctx, verbose):
    """Show my own user information"""
    result = ctx.obj['nc'].me()[0]
    if verbose >= 1:
        print_object( result )
    else:
        print_object( result, exclude=['APIKey'], only=ctx.obj['show_only'] )


@vsdcli.command(name='free-api')
@click.argument('ressource', metavar='<ressource>', required=True)
@click.option('--verb',
              type=click.Choice(['PUT',
                                 'GET',
                                 'POST',
                                 'DELETE']),
              default='GET',
              help='Default : GET')
@click.option('--header', metavar='<name:value>', help='Add header to the request. Can be repeated.')
@click.option('--key-value', metavar='<key:value>', multiple=True, help='Specify body in key/value pair. Can be repeated. Incompatible with --body.')
@click.option('--body', metavar='<data json>', help='Specify body of the request in json format. Incompatible with --key-value.')
@click.pass_context
def free_api(ctx, ressource, verb, header, key_value, body):
    """build your own API call (with headers and data)"""
    import json
    if key_value and body:
        raise click.exceptions.UsageError(
            "Use body or key-value")
    if key_value:
        params = {}
        for kv in key_value:
            key, value = kv.split(':',1)
            params[key] = value
    if body:
        try:
            params = json.loads(body)
        except ValueError:
            raise click.exceptions.UsageError(
                "Body could not be decoded as JSON")
    if verb == 'GET':
        result = ctx.obj['nc'].get(ressource)
    elif verb == 'PUT':
        result = ctx.obj['nc'].put(ressource, params)
    elif verb == 'POST':
        result = ctx.obj['nc'].post(ressource, params)
    elif verb == 'DELETE':
        result = ctx.obj['nc'].delete(ressource)
    print json.dumps(result, indent=4)

