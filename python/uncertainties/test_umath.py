"""
Tests of the code in uncertainties.umath.

These tests can be run through the Nose testing framework.

(c) 2010-2013 by Eric O. LEBIGOT (EOL).
"""

from __future__ import division

# Standard modules
import sys
import math

# Local modules:
import uncertainties
import uncertainties.umath as umath
from uncertainties import ufloat
from uncertainties import __author__

import test_uncertainties

###############################################################################
# Unit tests
    
def test_fixed_derivatives_math_funcs():
    """
    Comparison between function derivatives and numerical derivatives.

    This comparison is useful for derivatives that are analytical.
    """

    for name in umath.many_scalars_to_scalar_funcs:
        # print "Checking %s..." % name
        func = getattr(umath, name)
        # Numerical derivatives of func: the nominal value of func() results
        # is used as the underlying function:
        numerical_derivatives = uncertainties.NumericalDerivatives(
            lambda *args: func(*args))
        test_uncertainties._compare_derivatives(func, numerical_derivatives)

    # Functions that are not in umath.many_scalars_to_scalar_funcs:

    ##
    # modf(): returns a tuple:
    def frac_part_modf(x):
        return umath.modf(x)[0]
    def int_part_modf(x):
        return umath.modf(x)[1]
    
    test_uncertainties._compare_derivatives(
        frac_part_modf,
        uncertainties.NumericalDerivatives(
            lambda x: frac_part_modf(x)))
    test_uncertainties._compare_derivatives(
        int_part_modf,
        uncertainties.NumericalDerivatives(
            lambda x: int_part_modf(x)))
    
    ##
    # frexp(): returns a tuple:
    def mantissa_frexp(x):
        return umath.frexp(x)[0]
    def exponent_frexp(x):
        return umath.frexp(x)[1]
    
    test_uncertainties._compare_derivatives(
        mantissa_frexp,
        uncertainties.NumericalDerivatives(
            lambda x: mantissa_frexp(x)))
    test_uncertainties._compare_derivatives(
        exponent_frexp,
        uncertainties.NumericalDerivatives(
            lambda x: exponent_frexp(x)))

def test_compound_expression():
    """
    Test equality between different formulas.
    """
    
    x = ufloat(3, 0.1)
    
    # Prone to numerical errors (but not much more than floats):
    assert umath.tan(x) == umath.sin(x)/umath.cos(x)

    
def test_numerical_example():
    "Test specific numerical examples"

    x = ufloat(3.14, 0.01)
    result = umath.sin(x)
    # In order to prevent big errors such as a wrong, constant value
    # for all analytical and numerical derivatives, which would make
    # test_fixed_derivatives_math_funcs() succeed despite incorrect
    # calculations:
    assert ("%.6f +/- %.6f" % (result.nominal_value, result.std_dev)
            == "0.001593 +/- 0.010000")

    # Regular calculations should still work:
    assert("%.11f" % umath.sin(3) == "0.14112000806")

def test_monte_carlo_comparison():
    """
    Full comparison to a Monte-Carlo calculation.

    Both the nominal values and the covariances are compared between
    the direct calculation performed in this module and a Monte-Carlo
    simulation.
    """
    
    try:
        import numpy
        import numpy.random
    except ImportError:
        import warnings
        warnings.warn("Test not performed because NumPy is not available")
        return

    # Works on numpy.arrays of Variable objects (whereas umath.sin()
    # does not):
    sin_uarray_uncert = numpy.vectorize(umath.sin, otypes=[object])
    
    # Example expression (with correlations, and multiple variables combined
    # in a non-linear way):
    def function(x, y):
        """
        Function that takes two NumPy arrays of the same size.
        """
        # The uncertainty due to x is about equal to the uncertainty
        # due to y:
        return 10 * x**2 - x * sin_uarray_uncert(y**3)

    x = ufloat(0.2, 0.01)
    y = ufloat(10, 0.001)
    function_result_this_module = function(x, y)
    nominal_value_this_module = function_result_this_module.nominal_value

    # Covariances "f*f", "f*x", "f*y":
    covariances_this_module = numpy.array(uncertainties.covariance_matrix(
        (x, y, function_result_this_module)))

    def monte_carlo_calc(n_samples):
        """
        Calculate function(x, y) on n_samples samples and returns the
        median, and the covariances between (x, y, function(x, y)).
        """
        # Result of a Monte-Carlo simulation:
        x_samples = numpy.random.normal(x.nominal_value, x.std_dev,
                                        n_samples)
        y_samples = numpy.random.normal(y.nominal_value, y.std_dev,
                                        n_samples)
        function_samples = function(x_samples, y_samples)

        cov_mat = numpy.cov([x_samples, y_samples], function_samples)
        
        return (numpy.median(function_samples), cov_mat)
        
    (nominal_value_samples, covariances_samples) = monte_carlo_calc(1000000)


    ## Comparison between both results:

    # The covariance matrices must be close:

    # We rely on the fact that covariances_samples very rarely has
    # null elements:
    
    assert numpy.vectorize(test_uncertainties._numbers_close)(
        covariances_this_module,
        covariances_samples,
        0.05).all(), (
        "The covariance matrices do not coincide between"
        " the Monte-Carlo simulation and the direct calculation:\n"
        "* Monte-Carlo:\n%s\n* Direct calculation:\n%s"
        % (covariances_samples, covariances_this_module)
        )
    
    # The nominal values must be close:
    assert test_uncertainties._numbers_close(
        nominal_value_this_module,
        nominal_value_samples,
        # The scale of the comparison depends on the standard
        # deviation: the nominal values can differ by a fraction of
        # the standard deviation:
        math.sqrt(covariances_samples[2, 2])
        / abs(nominal_value_samples) * 0.5), (
        "The nominal value (%f) does not coincide with that of"
        " the Monte-Carlo simulation (%f), for a standard deviation of %f."
        % (nominal_value_this_module,
           nominal_value_samples,
           math.sqrt(covariances_samples[2, 2]))
        )

    
def test_math_module():
    "Operations with the math module"

    x = ufloat(-1.5, 0.1)
    
    # The exponent must not be differentiated, when calculating the
    # following (the partial derivative with respect to the exponent
    # is not defined):
    assert (x**2).nominal_value == 2.25

    # Regular operations are chosen to be unchanged:
    assert isinstance(umath.sin(3), float)

    # Python >=2.6 functions:

    if sys.version_info >= (2, 6):
    
        # factorial() must not be "damaged" by the umath module, so as 
        # to help make it a drop-in replacement for math (even though 
        # factorial() does not work on numbers with uncertainties 
        # because it is restricted to integers, as for 
        # math.factorial()):
        assert umath.factorial(4) == 24

        # Boolean functions:
        assert not umath.isinf(x)

        # Comparison, possibly between an AffineScalarFunc object and a
        # boolean, which makes things more difficult for this code:
        assert umath.isinf(x) == False

        # fsum is special because it does not take a fixed number of
        # variables:
        assert umath.fsum([x, x]).nominal_value == -3

    # The same exceptions should be generated when numbers with uncertainties
    # are used:

    ## !! The Nose testing framework seems to catch an exception when
    ## it is aliased: "exc = OverflowError; ... except exc:..."
    ## surprisingly catches OverflowError. So, tests are written in a
    ## version-specific manner (until the Nose issue is resolved).

    if sys.version_info < (2, 6):
            
        try:
            math.log(0)
        except OverflowError, err_math:  # "as", for Python 2.6+
            pass
        else:
            raise Exception('OverflowError exception expected')
        try:
            umath.log(0)
        except OverflowError, err_ufloat:  # "as", for Python 2.6+
            assert err_math.args == err_ufloat.args
        else:
            raise Exception('OverflowError exception expected')
        try:
            umath.log(ufloat(0, 0))
        except OverflowError, err_ufloat:  # "as", for Python 2.6+
            assert err_math.args == err_ufloat.args
        else:
            raise Exception('OverflowError exception expected')
        try:
            umath.log(ufloat(0, 1))
        except OverflowError, err_ufloat:  # "as", for Python 2.6+
            assert err_math.args == err_ufloat.args
        else:
            raise Exception('OverflowError exception expected')

    else:

        try:
            math.log(0)
        except ValueError, err_math:  # Python 2.6+: as err_math
            # Python 3 does not make exceptions local variables: they are
            # restricted to their except block:
            err_math_args = err_math.args
        else:
            raise Exception('ValueError exception expected')

        try:
            umath.log(0)
        except ValueError, err_ufloat:  # Python 2.6+: as err_math
            assert err_math_args == err_ufloat.args
        else:
            raise Exception('ValueError exception expected')
        try:
            umath.log(ufloat(0, 0))
        except ValueError, err_ufloat:  # Python 2.6+: as err_math
            assert err_math_args == err_ufloat.args
        else:
            raise Exception('ValueError exception expected')
        try:
            umath.log(ufloat(0, 1))
        except ValueError, err_ufloat:  # Python 2.6+: as err_math
            assert err_math_args == err_ufloat.args
        else:
            raise Exception('ValueError exception expected')

    
def test_hypot():
    '''
    Special cases where derivatives cannot be calculated:
    '''
    x = ufloat(0, 1)
    y = ufloat(0, 2)
    # Derivatives that cannot be calculated simply return NaN, with no
    # exception being raised, normally:
    result = umath.hypot(x, y)
    assert test_uncertainties.isnan(result.derivatives[x])
    assert test_uncertainties.isnan(result.derivatives[y])

def test_power_all_cases():
    '''
    Test special cases of umath.pow().
    '''
    test_uncertainties.power_all_cases(umath.pow)

# test_power_special_cases() is similar to
# test_uncertainties.py:test_power_special_cases(), but with small
# differences: the built-in pow() and math.pow() are slightly
# different:
def test_power_special_cases():
    '''
    Checks special cases of umath.pow().
    '''
    
    test_uncertainties.power_special_cases(umath.pow)

    # We want the same behavior for numbers with uncertainties and for
    # math.pow() at their nominal values:

    positive = ufloat(0.3, 0.01)
    negative = ufloat(-0.3, 0.01)
    
    # http://stackoverflow.com/questions/10282674/difference-between-the-built-in-pow-and-math-pow-for-floats-in-python

    try:
        umath.pow(ufloat(0, 0.1), negative)
    except (ValueError, OverflowError), err:  # Python 2.6+ "as err"
        err_type = type(err)  # For Python 3: err is destroyed after except
    else:
        err_type = None
        
    err_msg = 'A proper exception should have been raised'

    # An exception must have occurred:
    if sys.version_info >= (2, 6):
        assert err_type == ValueError, err_msg
    else:
        assert err_type == OverflowError, err_msg
            
    try:
        result = umath.pow(negative, positive)
    except ValueError:
        # The reason why it should also fail in Python 3 is that the
        # result of Python 3 is a complex number, which uncertainties
        # does not handle (no uncertainties on complex numbers). In
        # Python 2, this should always fail, since Python 2 does not
        # know how to calculate it.
        pass
    else:
        if sys.version_info >= (2, 6):
            raise Exception('A proper exception should have been raised')
        else:
            assert test_uncertainties.isnan(result.nominal_value)
            assert test_uncertainties.isnan(result.std_dev)
    
def test_power_wrt_ref():
    '''
    Checks special cases of the umath.pow() power operator.
    '''
    test_uncertainties.power_wrt_ref(umath.pow, math.pow)
    
