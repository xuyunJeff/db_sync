# !/usr/bin/python3
import asyncio
import logging
import optparse
import sys

from schemaobject import connection, SchemaObject
from syncdb import *
from utils import *

__author__ = """
Mitch Matuson
Mustafa Ozgur
"""
__copyright__ = """
Copyright 2009-2016 Mitch Matuson
Copyright 2016 Mustafa Ozgur
"""
__version__ = "0.9.4"
__license__ = "Apache 2.0"

APPLICATION_VERSION = __version__
APPLICATION_NAME = "Schema Sync"
LOG_FILENAME = "schemasync.log"
DATE_FORMAT = "%Y%m%d"
TPL_DATE_FORMAT = "%a, %b %d, %Y"
PATCH_TPL = """--
-- Schema Sync %(app_version)s %(type)s
-- Created: %(created)s
-- Server Version: %(server_version)s
-- Apply To: %(target_host)s/%(target_database)s
--

%(data)s"""


def parse_cmd_line():
    """Parse the command line options and pass them to the application"""

    usage = """
            %prog [options] <source> <target>
            source/target format: mysql://user:pass@host:port/database"""
    description = """
                   A MySQL Schema Synchronization Utility
                  """
    parser = optparse.OptionParser(usage=usage,
                                   description=description)

    parser.add_option("-V", "--version",
                      action="store_true",
                      dest="show_version",
                      default=False,
                      help="show version and exit.")

    parser.add_option("-t", "--tables",
                      dest="tables",
                      help="sync multi tables.")

    parser.add_option("-r", "--revision",
                      action="store_true",
                      dest="version_filename",
                      default=False,
                      help=("increment the migration script version number "
                            "if a file with the same name already exists."))

    parser.add_option("-w", "--sync-views",
                      dest="sync_views",
                      action="store_true",
                      default=False,
                      help="sync the schema views.")

    parser.add_option("-g", "--sync-triggers",
                      dest="sync_triggers",
                      action="store_true",
                      default=False,
                      help="sync the schema trigger.")

    parser.add_option("-p", "--sync-procedure",
                      dest="sync_procedure",
                      action="store_true",
                      default=False,
                      help="sync the schema procedure.")

    parser.add_option("-a", "--sync-auto-inc",
                      dest="sync_auto_inc",
                      action="store_true",
                      default=False,
                      help="sync the AUTO_INCREMENT value for each table.")

    parser.add_option("-c", "--sync-comments",
                      dest="sync_comments",
                      action="store_true",
                      default=False,
                      help=("sync the COMMENT field for all "
                            "tables AND columns"))

    parser.add_option("-D", "--no-date",
                      dest="no_date",
                      action="store_true",
                      default=False,
                      help="removes the date from the file format ")

    parser.add_option("--charset",
                      dest="charset",
                      default='utf8',
                      help="set the connection charset, default: utf8")

    parser.add_option("--tag",
                      dest="tag",
                      help=("tag the migration scripts as <database>_<tag>."
                            " Valid characters include [A-Za-z0-9-_]"))

    parser.add_option("--output-directory",
                      dest="output_directory",
                      default=os.getcwd(),
                      help=("directory to write the migration scrips. "
                            "The default is current working directory. "
                            "Must use absolute path if provided."))

    parser.add_option("--log-directory",
                      dest="log_directory",
                      help=("set the directory to write the log to. "
                            "Must use absolute path if provided. "
                            "Default is output directory. "
                            "Log filename is schemasync.log"))

    options, args = parser.parse_args(sys.argv[1:])

    if options.show_version:
        print(APPLICATION_NAME, __version__)
        return 0

    if (not args) or (len(args) != 2):
        parser.print_help()
        return 0

    return args, dict(version_filename=options.version_filename,
                      tables=options.tables,
                      output_directory=options.output_directory,
                      log_directory=options.log_directory,
                      no_date=options.no_date,
                      tag=options.tag,
                      charset=options.charset,
                      sync_auto_inc=options.sync_auto_inc,
                      sync_comments=options.sync_comments)


async def app(sourcedb='', targetdb='', tables='', version_filename=False,
              output_directory=None, log_directory=None, no_date=False,
              tag=None, charset=None, sync_views=False, sync_procedures=False, sync_triggers=False, sync_auto_inc=False,
              sync_comments=False):
    """Main Application"""

    options = locals()

    if not os.path.isabs(output_directory):
        print
        "Error: Output directory must be an absolute path. Quiting."
        return 1

    if not os.path.isdir(output_directory):
        print
        "Error: Output directory does not exist. Quiting."
        return 1

    if not log_directory or not os.path.isdir(log_directory):
        if log_directory:
            print
            "Log directory does not exist, writing log to %s" % output_directory
        log_directory = output_directory

    logging.basicConfig(filename=os.path.join(log_directory, LOG_FILENAME),
                        level=logging.INFO,
                        format='[%(levelname)s  %(asctime)s] %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(console)

    if not sourcedb:
        logging.error("Source database URL not provided. Exiting.")
        return 1

    source_info = connection.parse_database_url(sourcedb)
    if not source_info:
        logging.error("Invalid source database URL format. Exiting.")
        return 1

    if not source_info['protocol'] == 'mysql':
        logging.error("Source database must be MySQL. Exiting.")
        return 1

    if 'db' not in source_info:
        logging.error("Source database name not provided. Exiting.")
        return 1

    if not targetdb:
        logging.error("Target database URL not provided. Exiting.")
        return 1

    target_info = connection.parse_database_url(targetdb)
    if not target_info:
        logging.error("Invalid target database URL format. Exiting.")
        return 1

    if not target_info['protocol'] == 'mysql':
        logging.error("Target database must be MySQL. Exiting.")
        return 1

    if 'db' not in target_info:
        logging.error("Target database name not provided. Exiting.")
        return 1

    source_obj = SchemaObject()
    target_obj = SchemaObject()

    srcfut = asyncio.ensure_future(source_obj.build_database(sourcedb, charset, table_names=tables))
    tagfut = asyncio.ensure_future(target_obj.build_database(targetdb, charset, table_names=tables))

    await asyncio.gather(srcfut, tagfut)

    if compare_version(source_obj.version, '5.0.0') < 0:
        logging.error("%s requires MySQL version 5.0+ (source is v%s)"
                      % (APPLICATION_NAME, source_obj.version))
        return 1

    if compare_version(target_obj.version, '5.0.0') < 0:
        logging.error("%s requires MySQL version 5.0+ (target is v%s)"
                      % (APPLICATION_NAME, target_obj.version))
        return 1

    # data transformation filters
    filters = (lambda d: REGEX_MULTI_SPACE.sub(' ', d),
               lambda d: REGEX_DISTANT_SEMICOLIN.sub(';', d),
               lambda d: REGEX_SEMICOLON_EXPLODE_TO_NEWLINE.sub(";\n", d))

    # Information about this run, used in the patch/revert templates
    ctx = dict(app_version=APPLICATION_VERSION,
               server_version=target_obj.version,
               target_host=target_obj.host,
               target_database=target_obj.selected.name,
               created=datetime.datetime.now().strftime(TPL_DATE_FORMAT))

    p_fname, r_fname = create_pnames(target_obj.selected.name,
                                     tag=tag,
                                     date_format=DATE_FORMAT,
                                     no_date=no_date)

    ctx['type'] = "Patch Script"
    p_buffer = PatchBuffer(name=os.path.join(output_directory, p_fname),
                           filters=filters, tpl=PATCH_TPL, ctx=ctx.copy(),
                           version_filename=version_filename)

    ctx['type'] = "Revert Script"
    r_buffer = PatchBuffer(name=os.path.join(output_directory, r_fname),
                           filters=filters, tpl=PATCH_TPL, ctx=ctx.copy(),
                           version_filename=version_filename)

    db_selected = False

    for patch, revert in sync_schema(source_obj.selected,
                                     target_obj.selected, options):
        if patch and revert:
            if not db_selected:
                p_buffer.write(target_obj.selected.select() + '\n')
                r_buffer.write(target_obj.selected.select() + '\n')
                p_buffer.write(target_obj.selected.fk_checks(0) + '\n')
                r_buffer.write(target_obj.selected.fk_checks(0) + '\n')
                db_selected = True

            p_buffer.write(patch + '\n')
            r_buffer.write(revert + '\n')

    if db_selected:
        p_buffer.write(target_obj.selected.fk_checks(1) + '\n')
        r_buffer.write(target_obj.selected.fk_checks(1) + '\n')

    if options['sync_views']:
        for patch, revert in sync_views(source_obj.selected, target_obj.selected):
            if patch and revert:
                if not db_selected:
                    p_buffer.write(target_obj.selected.select() + '\n')
                    r_buffer.write(target_obj.selected.select() + '\n')
                    db_selected = True

                p_buffer.write(patch + '\n')
                r_buffer.write(revert + '\n')

    if options['sync_triggers']:
        for patch, revert in sync_triggers(source_obj.selected, target_obj.selected):
            if patch and revert:
                if not db_selected:
                    p_buffer.write(target_obj.selected.select() + '\n')
                    r_buffer.write(target_obj.selected.select() + '\n')
                    db_selected = True

                p_buffer.write(patch + '\n')
                r_buffer.write(revert + '\n')

    if options['sync_procedures']:
        for patch, revert in sync_procedures(source_obj.selected, target_obj.selected):
            if patch and revert:
                if not db_selected:
                    p_buffer.write(target_obj.selected.select() + '\n')
                    r_buffer.write(target_obj.selected.select() + '\n')
                    p_buffer.write(target_obj.selected.fk_checks(0) + '\n')
                    r_buffer.write(target_obj.selected.fk_checks(0) + '\n')
                    db_selected = True

                p_buffer.write(patch + '\n')
                r_buffer.write(revert + '\n')

    if not p_buffer.modified:
        logging.info(("No migration scripts written."
                      " mysql://%s/%s and mysql://%s/%s were in sync.") %
                     (source_obj.host, source_obj.selected.name,
                      target_obj.host, target_obj.selected.name))
    else:
        try:
            p_buffer.save()
            r_buffer.save()
            logging.info("Migration scripts created for mysql://%s/%s\n"
                         "Patch Script: %s\nRevert Script: %s"
                         % (target_obj.host, target_obj.selected.name,
                            p_buffer.name, r_buffer.name))
        except OSError as e:
            p_buffer.delete()
            r_buffer.delete()
            logging.error("Failed writing migration scripts. %s" % e)
            return 1

    return 0


async def main():
    try:
        args, argv = parse_cmd_line()
        await app(*args, **argv)
    except connection.DatabaseError as e:
        logging.error("MySQL Error %d: %s" % (e.args[0], e.args[1]))
        sys.exit(1)
    except KeyboardInterrupt:
        print("Sync Interrupted, Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    start = datetime.datetime.now()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    deltar = datetime.datetime.now() - start
    print(deltar)

'''
-c
--charset=utf8
mysql://root:zhonglixuntaqianbaidu@202.61.86.189:5179/saasops_manage
mysql://root:zhonglixuntaqianbaidu@202.61.86.189:5179/saasops_lb
--tag
202-61-86-189-tpre-200702
--tables
t_bs_area,t_bs_bank,t_bs_financialcode,t_cp_company,t_cp_site,t_cp_siteurl,t_gm_api,
t_gm_apiprefix,t_gm_case,t_gm_caseapi,t_gm_cat,t_gm_code,t_gm_depot,t_gm_depotcat,
t_gm_game,t_op_acttmpl,t_op_pay,t_op_payBankRelation,t_op_payWebSiteRelation
'''
