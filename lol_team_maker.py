import pandas as pd
import numpy as np
import pylab as pl
import sys
import time
import random
import itertools

def get_elo_value(row):
	tier_elo = {
		'Unranked':1200,
		'Bronze':800,
		'Silver':1150,
		'Gold':1500,
		'Platinum':1850,
		'Diamond':2200,
		'Master':2550
		}
	div_elo = {
		'Unranked':0,
		'5':0,
		'4':70,
		'3':140,
		'2':210,
		'1':280
	}

	elo = tier_elo[row['tier']]+div_elo[row['division']]

	return elo

def elo_score(possible_group,num_teams,team_size,data):
	team_elo = [0 for x in range(num_teams)]
	for i in range(num_teams):
		for j in range(team_size):
			team_elo[i] += data.ix[possible_group[i][j]].elo

	elo_dist_quality = np.std(team_elo)/data.elo.describe()['std']
	return team_elo, elo_dist_quality

def reweight(role_pref):
	if role_pref == 3:
		return 1.5
	elif role_pref == 2:
		return 1.0
	elif role_pref == 1:
		return 0.5
	else:
		return 0.1

def role_score(possible_group,num_teams,team_size,data):
	#reweight role preferences
	data.top = data.top.apply(reweight)
	data.jungle = data.jungle.apply(reweight)
	data.mid = data.mid.apply(reweight)
	data.adc = data.adc.apply(reweight)
	data.support = data.support.apply(reweight)

	#import pdb;pdb.set_trace()

	#find optimal role distribution for each team
	group_roles = [[] for x in range(num_teams)]
	role_scores = [[] for x in range(num_teams)]
	role_permutations = list(itertools.permutations(['top','jungle','mid','adc','support'],5))
	for i in range(num_teams):
		#assign role permutations
		best_permutation_score = 0
		for j in range(len(role_permutations)):
			permutation_score = 1
			team_roles = ['' for x in range(team_size)]
			for k in range(team_size):
				team_roles[k] = role_permutations[j][k]
				#import pdb;pdb.set_trace()
				#try:
				permutation_score *= data.ix[possible_group[i][k]][role_permutations[j][k]]
				#except:
					#import pdb;pdb.set_trace()
			if permutation_score > best_permutation_score:
				group_roles[i] = team_roles
				best_permutation_score = permutation_score
		role_scores[i]=best_permutation_score

	role_dist_quality = np.std(role_scores)
	return group_roles, role_dist_quality

data = pd.read_csv('/home/amery/Documents/responses.csv')
data=data.loc[0:24]

#stupid labels
data.columns = ['timestamp','shit','email','username','tier','division','top','jungle','mid','adc','support','agree']
data.set_index('username',inplace=True)
num_summoners = data.count()[0]

team_size = 5
num_teams = num_summoners/(team_size*1.0)

if ~np.equal(np.mod(num_teams,5),0):
	print "Make sure number of participants is a multiple of 5. Pad with eboard if needed."
	sys.exit(0)
else:
	num_teams = int(num_teams)



data['elo'] = data.apply(lambda row:get_elo_value(row),axis=1)

print('cool elo stats! :')
print data.elo.describe()

def find_optimal_group(team_size,num_teams):
	optimization_start = time.time()
	current_best_score = np.inf
	current_best_group = []
	current_best_roles = []
	#number of tries per run
	num_tries = 100
	
	for z in range(num_tries):
		possible_group = [[0 for x in range(team_size)] for x in range(num_teams)]

		random_order = range(len(data.index))
		random.shuffle(random_order)

		counter = 0
		for i in range(num_teams):
			for j in range(team_size):
				possible_group[i][j] = data.index[random_order[counter]]
				counter+=1

		#calculate permutation quality
		possible_group_elo,possible_group_edq = elo_score(possible_group,num_teams,team_size,data)
		possible_group_roles,possible_group_rdq = role_score(possible_group,num_teams,team_size,data)

		possible_group_score = possible_group_edq*possible_group_rdq

		#lower is better
		if possible_group_score < current_best_score:
			#then update current best variables
			current_best_group = possible_group
			current_best_score = possible_group_score
			current_best_roles = possible_group_roles


		current_elapsed = time.time()-optimization_start

		if (z/(num_tries*1.0))<=1:
			sys.stdout.write("\r%.2f%% completed, %d/%d permutations, elapsed: %.2fs" % (z/(num_tries)*100,z,num_tries,current_elapsed))
			sys.stdout.flush()

		#num_cycles=1
		#if z>num_cycles*num_tries:
		#	print "\nno solution found in %d tries, go debug" % (num_cycles*num_tries)
		#	sys.exit(0)

	return current_best_group,current_best_roles

final_groups,suggested_roles = find_optimal_group(team_size,num_teams)

#print everything nicely
print ''
for i in range(num_teams):
	print 'Team ' + str(i+1)
	for j in range(team_size):
		print final_groups[i][j] + ', ' + data.ix[final_groups[i][j]].tier + ' ' + data.ix[final_groups[i][j]].division + ', ' +suggested_roles[i][j]
	print ''