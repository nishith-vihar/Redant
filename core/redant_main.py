"""
This module takes care of:
1) Config file parsing (by gluster_test_parser).
2) Tests-to-run list preparation (by test_list_builder).
3) Invocation of the test_runner.
"""
import sys
import time
import datetime
import argparse
import pyfiglet
from halo import Halo
from environ import environ, FrameworkEnv
from parsing.params_handler import ParamsHandler
from test_list_builder import TestListBuilder
from test_runner import TestRunner
from result_handler import ResultHandler
from common.relog import Logger
sys.path.insert(1, ".")
sys.path.insert(1, "./common")


def pars_args():
    """
    Function to handle command line parsing for the redant.
    """

    parser = argparse.ArgumentParser(
        description='Redant test framework main script.')
    parser.add_argument("-c", "--config",
                        help="Config file(s) to read.",
                        action="store", dest="config_file",
                        default=None, type=str, required=True)
    parser.add_argument("-t", "--test-dir",
                        help="The test directory where TC(s) exist",
                        dest="test_dir", default=None, type=str, required=True)
    parser.add_argument("-sp", "--specific-test-path",
                        help="Path of the specific test to be run from tests/",
                        dest="spec_test", action='store_true', required=False)
    parser.add_argument("-l", "--log-dir",
                        help="The directory wherein log will be stored.",
                        dest="log_dir", default="/tmp/redant", type=str)
    parser.add_argument("-ll", "--log-level",
                        help="The log level. Default log level is Info",
                        dest="log_level", default="I", type=str)
    parser.add_argument("-cc", "--concurrency-count",
                        help="Number of concurrent test runs. Default is 2.",
                        dest="concur_count", default=2, type=int)
    parser.add_argument("-rf", "--result-file",
                        help="Result file. Default value is None",
                        dest="result_path", default=None, type=str)
    parser.add_argument("-xls", "--excel-sheet",
                        help="Spreadsheet for result. Default value is NULL",
                        dest="excel_sheet", default=None, type=str)
    return parser.parse_args()


def main():
    """
    Invocation order being.
    1. Parsing the command line arguments.
    2. Parsing the config file to get the configuration details.
    3. Invoking the test_list_builder to build the TC run order.
    4. Passing the details to the test_runner.
    """

    start = time.time()
    args = pars_args()

    spinner = Halo(spinner='dots')
    spinner.start("Starting param handling")
    try:
        param_obj = ParamsHandler(args.config_file)
    except IOError:
        print("Error: can't find config file or read data.")
        spinner.fail("IOError in param handling")
        return
    spinner.succeed("Param Handling Success.")

    spinner.start("Building test list")
    # Building the test list and obtaining the TC details.
    excluded_tests = param_obj.get_excluded_tests()
    TestListBuilder.create_test_dict(args.test_dir, excluded_tests,
                                     args.spec_test)
    spinner.succeed("Test List built")

    spinner.start("Creating log dirs")
    # Creating log dirs.
    args.log_dir = f'{args.log_dir}/{datetime.datetime.now()}'
    Logger.log_dir_creation(args.log_dir, TestListBuilder.get_test_path_list())
    spinner.succeed("Log dir creation successful.")

    # Framework Environment datastructure.
    env_obj = FrameworkEnv()
    env_obj.init_ds()

    # Environment setup.
    env_set = environ(param_obj, env_obj, f"{args.log_dir}/main.log",
                      args.log_level)
    env_set.setup_env()

    # invoke the test_runner.
    TestRunner.init(TestListBuilder, param_obj, env_set, args.log_dir,
                    args.log_level, args.concur_count, args.spec_test)
    result_queue = TestRunner.run_tests(env_obj)

    # Environment cleanup. TBD.
    total_time = time.time() - start
    ResultHandler.handle_results(
        result_queue, args.result_path, total_time, args.excel_sheet)

    env_set.teardown_env()


if __name__ == '__main__':
    print(pyfiglet.figlet_format("REDANT", font="slant"))
    main()
