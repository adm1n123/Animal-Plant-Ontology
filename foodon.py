import pandas as pd
import os
import random
import math
from scoring import Scoring

class FoodOn:
    """
    TODO: classes at leaf without entities are treated as entities. since they are not parent of any. It does not affect
    TODO: precision because those classes treated as entities in both candidate and skeleton candidate dict. what is the
    TODO: use of leaf class without entity, It should not be created.
    """


    def __init__(self):
        self.pairs_file = 'data/FoodOn/pairsfilesingle.txt' # save all pairs (parent, child) of FoodOn to here
        self.use_pairs_file = True  # don't generate again

        self.foodOn_root = 'root'   # root class we are working with.

        self.num_seeds = 2  # minimum number of labeled data for each class
        self.num_min_seeds = 1 # if total entities are less than num_seeds take this as number of seeds.

        self.pd_foodon_pairs = self.generate_pairs()
        self.all_classes, self.all_entities = self.get_classes_and_entities()   # all_entities are instances(not classes)
        self.digraph_root, self.class_dict, self.entity_dict = self.generate_digraph()


        # self.candidate_ontology_pkl = 'data/FoodOn/candidate_classes_dict.pkl'  # save ground truth ontology (excluding classes without entities) dict to here
        # self.skeleton_and_entities_pkl = 'data/FoodOn/skeleton_candidate_classes_dict.pkl'  # save skeleton ontology dict and entities to populate to here



    def generate_pairs(self):   # tested

        print('Using pre-generated pairs file.')
        df = pd.read_csv(self.pairs_file, sep='\t')
        df["Parent"] = df["Parent"].str.lower()
        df["Child"] = df["Child"].str.lower()
        return df


    def get_classes_and_entities(self):
        classes = self.pd_foodon_pairs['Parent'].tolist()   # every non-leaf is a class.
        classes = list(set(classes))
        classes.sort()
        print('Found %d classes.' % len(classes))

        child = self.pd_foodon_pairs['Child'].tolist()
        child = list(set(child))
        child.sort()
        entities = [c for c in child if c not in classes]   # child which is also parent is not leaf(instance)
        print('Found %d entities.' % len(entities))
        return classes, entities

    def generate_digraph(self):
        print('Generating Digraph')
        class_dict = {class_id: Class(class_id) for _, class_id in enumerate(self.all_classes)}
        entity_dict = {entity_id: Entity(entity_id) for _, entity_id in enumerate(self.all_entities)}

        for _, row in self.pd_foodon_pairs.iterrows():
            if row['Parent'] == row['Child']:
                print(row['Parent'], 'parent is child of itself')
                exit(0)
            if row['Parent'] in self.all_classes and row['Child'] in self.all_classes:  # both are classes
                parent = class_dict[row['Parent']]
                child = class_dict[row['Child']]
                parent.raw_label = row['Parent']
                child.raw_label = row['Child']
                parent.children.append(child)
                child.parents.append(parent)
            elif row['Parent'] in self.all_classes and row['Child'] in self.all_entities:
                parent = class_dict[row['Parent']]
                child = entity_dict[row['Child']]
                parent.raw_label = row['Parent']
                child.raw_label = row['Child']
                parent.all_entities.append(child)
                child.parents.append(parent)

        digraph = (class_dict[self.foodOn_root], class_dict, entity_dict)
        return digraph


    def seed_digraph(self):
        print('Seeding digraph.')
        seeds = set()
        count = 0
        for _, node in self.class_dict.items():
            if len(node.all_entities) > self.num_seeds:
                node.seed_entities = random.sample(node.all_entities, self.num_seeds)
            elif len(node.all_entities) > self.num_min_seeds:
                node.seed_entities = random.sample(node.all_entities, self.num_min_seeds)
            else:
                node.seed_entities = node.all_entities.copy()
            seeds = seeds.union(set(node.seed_entities))
            node.seed_count = len(node.seed_entities)
            if len(node.all_entities) == 0:
                count += 1

        non_seeds = set(self.entity_dict.values()) - seeds

        print(f'Classes without entities: {count}, classes with entities: {len(self.all_classes)-count}')
        digraph_seeded = (self.class_dict, list(non_seeds))
        print('seeds %d, Found %d non-seed entities to populate out of %d all entities.' % (len(seeds), len(non_seeds), len(self.all_entities)))
        return digraph_seeded

    def no_seed(self):
        print('not Seeding digraph.')
        seeds = set()
        count = 0

        non_seeds = set(self.entity_dict.values()) - seeds

        print(f'Classes without entities: {count}, classes with entities: {len(self.all_classes)-count}')
        digraph_seeded = (self.class_dict, list(non_seeds))
        print('seeds %d, Found %d non-seed entities to populate out of %d all entities.' % (len(seeds), len(non_seeds), len(self.all_entities)))
        return digraph_seeded

    def seed_digraph2(self):
        print('Seeding digraph.')
        seeds = set()
        count = 0
        # min_non_seeds = 1
        threshold, fraction = 1, .10 # if entities are more than 5 take 80% as seeds.
        for _, node in self.class_dict.items():
            if len(node.all_entities) > threshold:
                node.seed_entities = random.sample(node.all_entities, math.floor(len(node.all_entities)*fraction))
            else:
                node.seed_entities = node.all_entities.copy()

            seeds = seeds.union(set(node.seed_entities))

            if len(node.all_entities) == 0:
                count += 1

        non_seeds = set(self.entity_dict.values()) - seeds

        print(f'Classes without entities: {count}, classes with entities: {len(self.all_classes)-count}')
        digraph_seeded = (self.class_dict, list(non_seeds))
        print('seeds %d, Found %d non-seed entities to populate out of %d all entities.' % (len(seeds), len(non_seeds), len(self.all_entities)))
        return digraph_seeded

    def seed_digraph20_test(self):
        print('Seeding digraph.')
        seeds = set()
        count = 0

        for _, node in self.class_dict.items():
            if len(node.all_entities) <= 10:
                node.seed_entities = node.all_entities.copy()
            elif len(node.all_entities) < 30:
                node.seed_entities = random.sample(node.all_entities, 10)
            else:
                node.seed_entities = random.sample(node.all_entities, len(node.all_entities)-20)

            seeds = seeds.union(set(node.seed_entities))
            node.seed_count = len(node.seed_entities)
            if len(node.all_entities) == 0:
                count += 1

        non_seeds = set(self.entity_dict.values()) - seeds

        print(f'Classes without entities: {count}, classes with entities: {len(self.all_classes)-count}')
        digraph_seeded = (self.class_dict, list(non_seeds))
        print('seeds %d, Found %d non-seed entities to populate out of %d all entities.' % (len(seeds), len(non_seeds), len(self.all_entities)))
        return digraph_seeded

    def populate_foodon_digraph(self):

        # class_dict, non_seed_entities = self.seed_digraph2()
        # class_dict, non_seed_entities = self.seed_digraph()
        class_dict, non_seed_entities = self.no_seed()

        scoring = Scoring(
            root=self.digraph_root,
            class_dict=class_dict,
            entity_dict=self.entity_dict,
            non_seeds=non_seed_entities)    # entity assumed to belongs to one class.

        scoring.run_config()
        # scoring.run_analysis()
        # scoring.bad_precision()
        # scoring.find_worst_classes()
        # scoring.find_diff_old_rmv_method()
        # scoring.print_test_20()
        # scoring.find_per_class_prec()
        return

"""
All the parents of class/entity are considered.
"""
class Class:
    def __init__(self, ID):
        self.ID = ID  # class id
        self.raw_label = None
        self.label = None   # class label processed
        self.Lc = None
        self.Rc = None
        self.Sc = None
        self.seed_entities = [] # seed entities for this class
        self.seed_count = 0
        self.predicted_entities = []    # predicted entities for this class
        self.all_entities = []  # all entities in this class
        self.children = []  # all child subclasses(not entities)
        self.parents = []    # all parents
        self.visited = 0
        self.Rc_sum = None  # sum of all Rc vectors of subclasses with non-zero entities.
        self.Rc_count = 0   # count of all the classes in subtree with non-zero entities.
        self.in_path = False
        self.pre_proc = False   # vector Rc, Sc computed.
        self.visited_for = None
        self.all_words = True
        self.head = None


class Entity:
    def __init__(self, ID):
        self.ID = ID  # class id
        self.raw_label = None
        self.label = None   # entity label processed
        self.Le = None
        self.score = 0   # max score during traversal.
        self.predicted_class = None
        self.parents = []  # all parent classes
        self.visited_classes = 0
        self.all_words = True
        self.head = None



