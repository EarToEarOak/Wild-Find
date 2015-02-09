import sys


class Utils(object):
    # Print error and exit
    @staticmethod
    def error(error, fatal=True):
        if fatal:
            sys.exit(error)

        sys.stderr.write(error + '\n')

    # Return ranges based on tolerance
    @staticmethod
    def calc_tolerances(values, tolerance):
        valuesMin = [value * (100 - tolerance) / 100. for value in values]
        valuesMax = [value * (100 + tolerance) / 100. for value in values]
        return zip(valuesMax, valuesMin)
