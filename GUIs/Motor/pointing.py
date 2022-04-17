# Useful functions to work on and display pointing models:
# - Read all pointing models from the database and display their history
# - Load a specific model from database or file
# - Produce a plot of pointing corrections across the sky
# - Get pointing correction for given sky position
#
# author: Christopher van Eldik; modified by Cornelia Arcaro
#

import sys, os.path, os
import string, math, copy

import datetime as dt
import matplotlib.patches as mpatches
import matplotlib.dates as dates
import matplotlib.pyplot as plt

import numpy as np

#sys.path.append(os.environ["HESSROOT"])
#from dbgui.db import SimpleTable, MySQLconnection

param_names = ['amplitude SE-error Az (arcsec)',
              'phase SE-error AZ (deg)',
              'amplitude SE-error Alt (arcsec)',
              'phase SE-error Alt (deg)',
              'offset SE Az (arcsec)',
              'amplitude non-verticality Az-axis (arcsec)',
              'phase non-verticality Az-axis (deg)',
              'vertical camera offset (arcsec)',
              'vertical camera offset reverse (arcsec)',
              'horizontal camera offset (arcsec)',
              'amplitude non-verticality Alt-axis (arcsec)',
              'vertical bending (arcsec)',
              'horizontal bending (arcsec)',
              'refraction constant (arcsec)',
              'amplitude of sin(2 Az) effect (arcsec)',
              'mixing angle of sin(2 Az) effect (deg)',
              'phase of sin(2 Az) effect (deg)',
              'constant camera rotation (deg)',
              'constant focal length (m)',
              'parameter 19']

num_pointing_params = 20
    
degtorad = math.pi/180.0
radtodeg = 180.0/math.pi

    
class PointingModel:
    """
    Class that holds the parameters of a pointing model, provides
    a function to calculate pointing corrections for a particular coordinate,
    and enables loading of a model from the database or a file.
    """
    
    
    def __init__(self, numParams=19):
        """
        Initialise all variables to default values
        """
        self.numParams = numParams
        self.modelName = None
        self.telId = None
        self.whenEntered = dt.datetime(2000, 1, 1)
        self.from_date = dt.datetime(2000, 1, 1)
        self.to_date = dt.datetime(2000, 1, 1)
        self.active = None
        self.params = [None] * numParams
        
    
    def load_from_db(self, telId, date=None, dbuser='hess'):
        """
        Load a pointing model from database, given a telescope ID
        and the start of the period.
        The most recent (i.e. active) model is returned
        """
        
        try:
            mysql_connection = MySQLconnection(config=dbuser)
            mysql_connection.connect()
        except:
            print('There was a problem with connecting the database (user %s).' % dbuser)
            return

        # select the appropriate model.
        # If no date is given, load the one most recently stored,
        # which is not necessarily the one for the latest period.
        selection = 'Telescope=%d AND FunctionName="Pointing::MechanicalModel_Camera"' % telId
        if date != None:
            selection += ' AND Valid_From<="%s" AND Valid_Until>"%s"' % (date, date)

        try:
            
            PointingTable = SimpleTable("Astro_PointingCor", mysql_connection)
            id_columns = PointingTable.get_sets(order='WhenEntered', options='DESC', selection=selection)

            print(selection)
            print(id_columns)
            
            # read set IDs, take first (most recent) one, load the model information
            column = id_columns[0]
            self.whenEntered = dt.datetime.strptime(column[1], "%Y-%m-%d %H:%M:%S")
            self.telId = int(column[2])
            self.modelName = column[3]
            self.from_date = dt.datetime.strptime(column[4], "%Y-%m-%d %H:%M:%S")
            self.to_date = dt.datetime.strptime(column[5], "%Y-%m-%d %H:%M:%S")
            # self.numParams = column[6]

            self.params = [None] * self.numParams
          
            # load the model parameters
            setId = column[0]
            data = PointingTable.read_data(setId)
            for d in data:
                idx = int(d[0])
                value = float(d[1])
                self.params[idx] = value

        except:
            print('There was a problem with loading the data from the table.')
       
        mysql_connection.disconnect()
        
        
    def load_from_file(self, filename):
        """
        Reads a model from the file.
        """
        try:
            f = open(filename, 'r')
        except:
            print('Could not open file %s' % filename)
            return

        self.params = [None] * self.numParams
        
        try:
            self.modelName = f.readline().rstrip()
            self.telId = int(f.readline())
            self.from_date = dt.datetime.strptime(f.readline().rstrip(), "%Y-%m-%d %H:%M:%S")
            self.to_date = dt.datetime.strptime(f.readline().rstrip(), "%Y-%m-%d %H:%M:%S")
            for i in range(0, self.numParams):
                parString = f.readline().rstrip()
                (idx, value) = parString.split('\t')
                if int(idx) != i:
                    print('There was a problem reading parameter %d' % i)
                    return
                    
                self.params[i] = float(value)
            
        except:
            print('There was an error reading the model from file %s' % filename)
            return

    def __str__(self):
        return('PointingModel %s\n\tTelId:\t%d\n\tWhenEntered:\t%s\n\tValid_from:\t%s\n\tValid_to:\t%s' %\
                (self.modelName, self.telId, self.whenEntered.strftime('%Y-%m-%d %H:%M:%S'),\
                self.from_date.strftime('%Y-%m-%d %H:%M:%S'), self.to_date.strftime('%Y-%m-%d %H:%M:%S')))
    
    def print_parameters(self, reduced=False):
        """
        Print model parameters including description
        """
        
        params = self.get_parameters(reduced)
        for i in range(0, self.numParams):
            print('%s:\t%f' % (param_names[i], params[i]))
            

    def _get_correction(self, az, alt):
        """
        Implementation of the 19 parameters HESS mechanical pointing model.
        Takes single azimuth and altitude values as parameters.
        """
    
        az0 = az # in degrees
        alt0 = alt # in degrees
    
        # make sure that az is always positive
        # to correspond to HESS definition
        if az0 < 0:
            az0 += 360.
    
        # reverse
        sign = 1.0
        if alt0 > 90.0:
            sign = -1.0

        # SE-error AZ
        az1 = az0 + sign * self.params[0]/3600.0 * math.sin(degtorad * (az0 + self.params[1]))

        # SE-Error Alt: difficult to detangle from p10 !
        # p2 and p3 should be fixed
        alt1 = alt0 + sign * self.params[2]/3600.0 * math.sin(degtorad * (alt0 + self.params[3])) 

        # SE-offsets
        az2 = az1 + sign * self.params[4]/3600.0
        alt2 = alt1

        # not independent!
        # alt2 += fPars[xxx]/3600.;

        # reverse to normal
        if sign == -1.0:
            az0 +=  180.0
            if az0 > 360.0:
                az0 -= 360.0
    
            alt0 = 180. - alt0

            az2 +=  180.0
            if az2 > 360.0:
                az2 -= 360.0
        
            alt2 = 180. - alt2

        # non-verticality az-axis
        x1 = math.cos(degtorad * alt2) * math.cos(degtorad * az2)
        y1 = math.cos(degtorad * alt2) * math.sin(degtorad * az2)
        z1 = math.sin(degtorad * alt2)

        sina = math.sin(degtorad * self.params[5]/3600.0)
        cosa = math.cos(degtorad * self.params[5]/3600.0)

        sinb = sign * math.sin(degtorad * self.params[6])
        cosb = sign * math.cos(degtorad * self.params[6])

        x2 = x1 * ( (cosb*cosb) + (sinb*sinb)*cosa ) + y1 * ( sinb*cosb - cosa*sinb*cosb ) + z1 * ( -sina*sinb )
        y2 = x1 * ( sinb*cosb - cosa*sinb*cosb ) + y1 * ( (sinb*sinb) + cosa*(cosb*cosb)) + z1 * ( sina*cosb )
        z2 = x1 * ( sina*sinb ) + y1 * ( -sina*cosb ) + z1 * cosa

        altrad = math.asin( z2 )
        alt3   = radtodeg * altrad
        argument = x2 / math.cos( altrad )

        # dirty trick ...
        if argument > 1.0:
            argument = 1.0
        elif argument < -1.0:
            argument = -1.0

        if y2 > 0.0:
            az3 = radtodeg * math.acos(argument)
        else:
            az3 = 360. - radtodeg * math.acos(argument)

        # check az-range
        if az3 < 0.0:
            az3 +=360.0
        elif az3 > 360.0:
            az3 -= 360.0

        if (az3 > 330.0) and (az0 < 30.0):
            az3 -= 360.0
        if (az3 < 30.0) and (az0 > 330.0):
            az3 += 360.0

        # now camera system
        dy = alt3 - alt0 # vertical !
        dx = (az3 - az0) * math.cos(degtorad * alt3) # horizontal !
    
        # camera offsets
        # p8 only can be measured if normal + reverse mode data is available
        # p8 should be fix.
        dy += self.params[7]/3600.0 + sign * self.params[8]/3600.0
        dx += self.params[9]/3600.0

        # non-perpendicularity alt-axis   
        # difference in vertical direction is very small, neglected
        # dy += radtodeg * asin(cos(degtorad * fPars[10]) * sin(degtorad * alt3));
        dx += radtodeg * math.asin(math.sin(degtorad * self.params[10]/3600.0) * math.sin(degtorad * alt3))  

        # bending
        dy -= sign * self.params[11]/3600.0 * math.cos(degtorad * alt3)

        # horizontal bending not really needed. 
        # fix parameter p12
        dx += self.params[12]/3600.0 * math.cos(degtorad * alt3)

        # refraction : is yet corrected by measured weather! 
        # fix parameter p13
        dy += sign * self.params[13]/3600.0 * math.tan(degtorad * (90.0-alt3))

        # effect that depends on sin(2 az)
        dx += self.params[14]/3600.0 * math.cos(degtorad * self.params[15]) * math.sin(degtorad * 2 *(az3 + self.params[16]))
        dy += self.params[14]/3600.0 * math.sin(degtorad * self.params[15]) * math.sin(degtorad * 2 *(az3 + self.params[16]))

        dx *= degtorad # this is the correction in az
        dy *= degtorad # this is the correction in alt
    
        return (dx, dy)
    
    
    def get_correction(self, az, alt):
        """
        Vectorised version of _get_correction, which takes numpy
        arrays as input.
        """
        vecMechanicalModel = np.vectorize(self._get_correction)
        return vecMechanicalModel(az, alt)

    
    def get_parameters(self, reduced = False):
        """
        Return the vector of model parameters.
        If reduced is set to True, return parameters which are corrected
        for overflow in periodicity and for which amplitudes are converted
        to positive values.
        """
        
        if not reduced:
            return self.params
        
        params = copy.copy(self.params)
        
        # SE error
        params[1] = params[1] % 360.0
        if params[0] < 0:
            params[0] = math.fabs(params[0])
            params[1] = params[1] - 180.0
            
        # non-verticality az axis
        params[6] = params[6] % 360.0
        if params[5] < 0:
            params[5] = math.fabs(params[5])
            params[6] = params[6] - 180.0  
                
        # sin(2az) effect
        params[15] = params[15] % 360.0
        params[16] = params[16] % 180.0
        if params[14] < 0:
            params[14] = math.fabs(params[14])
            params[15] = (params[15] - 180.0) % 360.0
                
        if params[15] > 180.0:
            params[15] = params[15] - 180.0
            params[16] = (params[16] - 90.0) % 180.0

        return params
    

def plot_pointing_models(model_list, plot_difference=False, save_to_filename=None):
    """
    Plot the pointing corrections on the sky.
    model_list is a list of PointingModel objects.
    If plot_difference is True, the difference w.r.t.
    the first model is plotted.

    returns references to the two figures.
    """

    print('Plotting %d pointing models.' % len(model_list))

    # construct grid for arrow plotting
    az_lin  = np.linspace(-150., 180., 12)
    alt_lin = np.linspace(15., 75., 5)
    az, alt = np.meshgrid(az_lin, alt_lin)
    
    # 20 arcsec is 1 deg on the standard plot, 2 arcsec for the differencep plot
    scale_factor = 3600./20
    if plot_difference:
        scale_factor *= 10.


    #
    # Polar plot, zenith at the pole
    #
    fig0 = plt.figure(figsize=(10, 10))
    ax0 = fig0.add_subplot(111, projection='polar')
    ax0.set_theta_zero_location('N')
    ax0.set_theta_direction(-1)
    ax0.set_rlim(0,90.0)
    ax0.set_thetagrids(np.arange(0, 360, 30), labels=['N', r'$30^\circ$', r'$60^\circ$', 'E', r'$120^\circ$', r'$150^\circ$',\
                            'S', r'$-150^\circ$', r'$-120^\circ$', 'W', r'$-60^\circ$', r'$-30^\circ$'])
    ax0.set_rgrids(np.arange(15, 90, 15))
    ax0.grid(True)

    #
    # Mollweide projection
    #
    fig1 = plt.figure(figsize=(10, 10))
    ax1 = fig1.add_subplot(111, projection='mollweide')
    ax1.grid(True)
    ax1.set_xticklabels([r'$-150^\circ$', r'$-120^\circ$', 'W', r'$-60^\circ$', r'$-30^\circ$',\
                        'N', r'$30^\circ$', r'$60^\circ$', 'E', r'$120^\circ$', r'$150^\circ$'])
    
    is_ref = True
    is_first = True
    for (idx, model) in enumerate(model_list):

        (U, V) = model.get_correction(az, alt)
        U_copy = np.copy(U)
        V_copy = np.copy(V)

        # store first model as reference for plotting model differences
        if is_first:
            U_ref = np.copy(U)
            V_ref = np.copy(V)
            is_first = False

        if plot_difference:
            U -= U_ref
            V -= V_ref

        # keep this model as reference for the next model
        U_ref = U_copy
        V_ref = V_copy

        color = str('C%d' % idx)
        label = None 

        if plot_difference:
            
            if idx == 0:
                title = str('telescope pointing deviation (difference to model from %s)\n' % model.from_date.strftime('%Y-%m-%d %H:%M:%S'))
                title += '(arrow scale: 2 arcsecs/deg)'
            
            else: 
                label = str('CT%d %s' % (model.telId, model.from_date.strftime('%Y-%m-%d %H:%M:%S')))
        else:
            title = 'telescope pointing deviation (full model)\n'
            title += '(arrow scale: 20 arcsecs/deg)'
            label = str('CT%d %s' % (model.telId, model.from_date.strftime('%Y-%m-%d %H:%M:%S')))    
    
       # Polar plot
        ax0.quiver(az*radtodeg, 90.-alt, U, -V*radtodeg, angles='xy', scale_units='xy', scale=1./scale_factor,\
                       color=color, width=0.003, headwidth=3., headlength=5.,\
                       label=label)
        # plot direction of the azimuth axis
        if plot_difference == False:
            modelParams = model.get_parameters()
            azm_amplitude = modelParams[5] / 20.0
            azm_phase = (modelParams[6] + 90.0)*degtorad # do we really have to add 90deg to make it work?
            ax0.plot(azm_phase, azm_amplitude, '+', marker='p', markersize=10)
        
        # Mollweide projection
        ax1.quiver(az*degtorad, alt*degtorad, U, V, angles='xy', scale_units='xy', scale=1./scale_factor,color=color, width=0.003, headwidth=3., headlength=5.,label=label)

    ax0.legend(loc='lower right')
    ax1.legend(loc='lower right')
    ax0.set_title(title)
    ax1.set_title(title)

    plt.tight_layout()
    plt.show()
    return (fig0, fig1)



def read_model_list_from_db(telescope, dbuser="hess"):
    """
    Set up MySQL connection and query the Astro_PointingCor database.
    Sort pointing models in descending order of when they have been added to the database.

    Go through the list of stored models, and mark each model either as active (i.e. the most current model for a given period),
    or as outdated (meaning that there is one (or more) more recent model which is active).

    Periods are stored in a list, where each entry corresponds to a dictionary which stores the period's information including the model parameters.
    """
    
    mysql_connection = MySQLconnection(config=dbuser)
    mysql_connection.connect()

    selection = 'Telescope=%d AND FunctionName="Pointing::MechanicalModel_Camera"' % telescope

    PointingTable = SimpleTable("Astro_PointingCor", mysql_connection)
    id_columns = PointingTable.get_sets(order='WhenEntered', options='DESC', selection=selection)
    
    periods = []
    for id in id_columns:
    
        new_period = {'set': id[0]}
        new_period['tel'] = telescope
        new_period['active'] = False
        accept = True

        # convert time strings into python dates
        try:
            new_period['whenentered'] = dt.datetime.strptime(id[1], "%Y-%m-%d %H:%M:%S")
            new_period['from_date'] = dt.datetime.strptime(id[4], "%Y-%m-%d %H:%M:%S")
            new_period['to_date'] = dt.datetime.strptime(id[5], "%Y-%m-%d %H:%M:%S")
        except:
            print('One of the date transformations did not work.')
            continue
  
        from_date = new_period['from_date']
        to_date = new_period['to_date']

        if new_period['from_date'] >= new_period['to_date']:
            print('from_date is larger or equal to_date!')
            continue

        # first period gets added in any case
        if len(periods) == 0:
            new_period['active'] = True
            
        else:
            
            # work on copy of interval, since it will be cut during
            # the overlap testing process
            from_date = new_period['from_date']
            to_date = new_period['to_date']
        
            # for each next period we check whether or not there is complete
            # overlap with the set of previously added periods. If so, the
            # period is marked outdated.
            for p in periods:
        
                # full overlap: reject immediately
                if from_date >= p['from_date'] and to_date <= p['to_date']:
                    accept = False
                    break
            
                # no overlap: test next interval
                if from_date >= p['to_date'] or to_date <= p['from_date']:
                    continue
        
                # partial overlap on lower end:
                # shorten interval and repeat search
                if from_date >= p['from_date']:
                    from_date = max(from_date, p['to_date'])
            
                # partial overlap on higher end
                # shorten interval and repeat search
                if to_date <= p['to_date']:
                    to_date = min(to_date, p['from_date'])

        # read the actual model parameters for this period
        data = PointingTable.read_data(new_period['set']) 
        params = [0] * num_pointing_params
        
        # read out parameters. Store in dictionary because
        for d in data:
            params[d[0]] = d[1]
    
        new_period['params'] = params

        # add period to list of periods
        if accept:
            new_period['active'] = True
            print('appending set %d for telescope CT%d' % (new_period['set'], telescope))
#        else:
#            print('appending set %d as duplicate for telescope CT%d' % (new_period['set'], telescope))
        
        periods.append(new_period)
    
    mysql_connection.disconnect()    
    return periods


def extract_model_params(periods, active_only=True, write_to_disk=True, Dir='./'):
    """
    Produce a list of pointing period start dates and corresponding model parameters.

    periods: list of pointing model periods as produced by e.g. read_model_list_from_db().

    returns: list of vector with following entries:
             telId, period from date, period to date, db set value, vector of model parameters
    """
    
    date_params = []
    telescope = -1
    
    for p in periods:
        telescope = p['tel']
        if active_only and not p['active']:
            continue
            
        date_params.append([p['tel'], p['from_date'], p['to_date'], p['set'], p['params']])

    if telescope < 0:
        print('No period read?')
        
    # sort parameter sets by ascending observation period
    date_params_sorted = sorted(date_params)
    
    # write active models to file
    if(write_to_disk):
        if active_only:
            f = open(str(Dir + 'ActiveModelsCT%d.dat' % telescope), 'w')
        else:
            f = open(str(Dir + 'AllModelsCT%d.dat' % telescope), 'w')

        for d in date_params_sorted:
            f.write('Pointing::MechanicalModel_Camera\n')
            f.write(str('%d\n' % telescope))
            # f.write(str(d[2]) + '\n') # MySQL set id
            f.write(d[1].strftime('%Y-%m-%d %H:%M:%S'))
            f.write('\n')
            f.write(d[2].strftime('%Y-%m-%d %H:%M:%S'))
            f.write('\n')
            for i in range(0, 19):
                f.write(str(i) + '\t')
                f.write(str((d[4])[i]))
                f.write('\n')
        
        f.close()

    # correct for overflows in phase angles and turn amplitudes to positive values
    for d in date_params_sorted:
        params = d[4]
        
        for idx, param in enumerate(params):
            
            # SE error
            params[1] = params[1] % 360.0
            if params[0] < 0:
                params[0] = math.fabs(params[0])
                params[1] = params[1] - 180.0
            
            # non-verticality az axis
            params[6] = params[6] % 360.0
            if params[5] < 0:
                params[5] = math.fabs(params[5])
                params[6] = params[6] - 180.0  
                
            # sin(2az) effect
            params[15] = params[15] % 360.0
            params[16] = params[16] % 180.0
            if params[14] < 0:
                params[14] = math.fabs(params[14])
                params[15] = (params[15] - 180.0) % 360.0
                
            if params[15] > 180.0:
                params[15] = params[15] - 180.0
                params[16] = (params[16] - 90.0) % 180.0
    
    return date_params_sorted



def plot_model_history(periods,outDir):
    """
    Plot the model history. Model time periods are plotted vs. the time when they have been entered to the database. Active models are highlighted.

    periods: list of pointing model periods as produced by e.g. read_model_list_from_db().
    """

    smallest_date = dates.date2num(dt.datetime(2017, 1, 1))
    largest_date = dates.date2num(dt.datetime(2000, 1, 1))

    fig, ax = plt.subplots(figsize=(14,7))

    # plot outdated models
    for p in periods:
        
        telescope = p['tel']
        plt_whenentered = dates.date2num(p['whenentered'])
        plt_from_date = dates.date2num(p['from_date'])
        plt_to_date = dates.date2num(p['to_date'])

        # remember plot scale for diagonal plotting
        if smallest_date >= plt_from_date:
            smallest_date = plt_from_date
        
        if largest_date <= plt_to_date:
            largest_date = plt_to_date

        if p['active']:
            continue

        ax.plot_date([plt_from_date, plt_to_date], [plt_whenentered, plt_whenentered], ydate=True, ls='-', color='gray', marker='|')

    # plot active models
    for p in periods:
        if not p['active']:
            continue
    
        plt_whenentered = dates.date2num(p['whenentered'])
        plt_from_date = dates.date2num(p['from_date'])
        plt_to_date = dates.date2num(p['to_date'])
        ax.plot_date([plt_from_date, plt_to_date], [plt_whenentered, plt_whenentered], ydate=True, ls='-', color='r', marker='|')
        
    # plot diagonal
    ax.plot_date([smallest_date, largest_date], [smallest_date, largest_date], ls='--', marker='None')

    ax.set_title(str("CT%d" % telescope))
    ax.set_xlabel('date of period (year)')
    ax.set_ylabel('date of last update (year)')

    red_patch = mpatches.Patch(color='red', label='Active Models')
    gray_patch = mpatches.Patch(color='gray', label='Outdated Models')
    ax.legend(handles=[red_patch, gray_patch])
    
    plt.tight_layout()
    plt.show()
    # fig.savefig(str('ModelHistoryCT%d.pdf' % telescope), dpi=150)
    # fig.savefig(str('ModelHistoryCT%d.png' % telescope), dpi=150)
    fig.savefig(str(outDir + 'ModelHistoryCT%d.png' % telescope), dpi=150)
