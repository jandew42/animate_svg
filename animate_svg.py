"""Automatically creates an animation interpolated between svg files.

Current version: 0.0.1
Current problem: any TODO

  === PLANS ===

0.0.2 will have interpolate read over, working in original plan, commented
0.0.3 will have interpolate support relative points
0.0.4 will have make_frame read over, working propely, commented
0.0.10 may create a method that generates parallel node sets

0.1.0 will transition points in paths

0.1.1 will properly test check_tag for paths
0.1.2 will use xpath for self.create_bijects
0.1.3 will create self.bjects by iterating recursively over entire trees

0.2.0 will transition paths in groups

0.3.0 will transition atributes of paths

  === CHANGELOG ===

0.0.0 (created version system when xpath and parse_path were working)
0.0.1 has self.bijects created in a separate method, with tests

"""

import re
import glob
import cairosvg
import moviepy.editor as mpy

class Transition:
    """Create a set of transitions between svg files.
    
    Typical Usage:
        import glob
        filenames = sorted(glob.glob("foo*.svg"))
        n_files = len(filenames)
        trans = Transition(filenames) # checks files, creates animation fncs
        for i in range(100*n_files):
            t = i / n_files
            svg_text = trans.make_frame(t)
            # Now create a frame for an animation using svg_text.
    """
    def __init__(self, filenames):
        """Initialize svg files, collecting transition data.

        filenames is a list of strings of files to open.

        Creates self.trees for which each item is a derivative of
        xml.etree.ElementTree corresponding to each files in filenames.
        Instructions for accessing data from such an object:
        
        for name,       node.tag is the type of node
        for values,     node['key'] == value, as a dictionary
        for navigation, node.children is the list of children nodes
        """
        self.trees = [cairosvg.parser.Tree(url=url) for url in filenames]
        self.verify_trees()
        self.create_bijects()

    def verify_trees(self):
        """Makes sure all trees have the same viewBox, number of children."""
        for tree in self.trees:
            
            if not self.trees[0]['viewBox'] == tree['viewBox']:
                raise ValueError("file {} has different viewBox {}"
                                 .format(tree.url, tree['viewBox']))
                                 
            if not len(self.trees[0].children) == len(tree.children):
                raise ValueError("file {} has different number of children {}"
                                 .format(tree.url, len(tree.children)))

    def create_bijects(self):
        """Creates a sequence of bijections to all trees.

        bijections are from self.trees[0] to each tree in self.trees
        and they choose which elements are to be interpolated between

        results are saved in self.bijects so that, for every i,j:
            self.trees[0].children[j] corresponds with
            self.trees[i].children[self.bijects[i][j]]
        """
        self.bijects = []
        for tree in self.trees:
            
            biject = {}
            for i, child0 in enumerate(self.trees[0].children):
                
                # matching on id is the best option
                if 'id' in child0:
                    for j, child in enumerate(tree.children):
                        if child0['id'] == child.get('id'):
                            if not self.check_tag(child0, child):
                                raise ValueError(\
                        "file {}: match {} by id does not match by check_tag"
                        .format(tree.url, self.get_xpath(child0)))
                            biject[i] = j
                            break
                    if i in biject: continue
                            
                # otherwise, match the first element meeting tag requirements
                for j, child in enumerate(tree.children):
                    if self.check_tag(child0, child):
                        biject[i] = j
                        break
                    if i in biject: continue
                
                raise ValueError("file {}: could not find a match for {}"
                                 .format(tree.url, self.get_xpath(child0)))
                
            self.bijects.append(biject)
    
    RE_C_WSP = "[\s,]+"
    N_INPUTS_FOR_PATH_COMMAND = {"M": 2,
                                 "Z": 0,
                                 "L": 2,
                                 "H": 1,
                                 "V": 1,
                                 "C": 6,
                                 "S": 4,
                                 "Q": 4,
                                 "T": 2,
                                 "A": 7}
    
    def path_str_to_data(self, string):
        """Splits path string into a list of command-tuples.
        
        Uses self.RE_C_WSP as a regular expression to parse data separation.
        Uses self.N_INPUTS_FOR_PATH_COMMAND as a dictionary of possible
            commands and how many separated data elements should follow.
        """
        RE_CMD = "[" + "".join(self.N_INPUTS_FOR_PATH_COMMAND.keys()) + "]"
        string = string.strip()

        out = []
        cmds = list(re.finditer(RE_CMD, string, re.IGNORECASE))
        cmd0 = cmds.pop(0)
        for cmd1 in cmds:

            # recognize the command and end if it was a close path command
            cmd = cmd0.group()
            n = self.N_INPUTS_FOR_PATH_COMMAND[cmd.upper()]
            if n == 0:
                out.append((cmd))
                return out

            # locate the data between the current and next commands
            start = cmd0.end()
            end  = cmd1.start()
            d = string[start:end].strip()

            # split data into numbers
            nums = list(map(float, re.split(self.RE_C_WSP, d)))
            assert n*(len(nums) // n) == len(nums)
            while nums:
                out.append((cmd, *nums[:n]))
                del nums[:n]
            cmd0 = cmd1

        ### run the loop once more for the final command

        # recognize the command and end if it was a close path command
        cmd = cmd0.group()
        n = self.N_INPUTS_FOR_PATH_COMMAND[cmd.upper()]
        if n == 0:
            out.append((cmd))
            return out

        # locate the data after the final command
        start = cmd0.end()
        d = string[start:].strip()

        # split data into numbers
        nums = list(map(float, re.split(self.RE_C_WSP, d)))
        assert n*(len(nums) // n) == len(nums)
        while nums:
            out.append((cmd, *nums[:n]))
            del nums[:n]

        return out

    def path_data_to_str(self, data):
        """Joins path data into a string of commands."""
        outstrings = []
        for datum in data:
            outstrings.append(datum[0])
            outstrings.extend(map(repr, datum[1:]))
        return " ".join(outstrings)
        
    def check_tag(self, node0, node1):
        """Verify that both nodes have the same tag and are comparable.
        
        Here's a list, per tag, as to what "comparable" means.
            path: must have the same sequence of instructions
                  (the points may differ, but the command letters cannot)
        """
        if node0.tag != node1.tag: return False
        if node0.tag == "path":
            data0 = self.path_str_to_data(node0['d'])
            data1 = self.path_str_to_data(node1['d'])
            if len(data0) != len(data1): return False
            for datum0, datum1 in zip(data0, data1):
                if datum0[0].upper() != datum1[0].upper(): return False
                if len(datum0) != len(datum1): return False
        return True
    
    @staticmethod
    def get_xpath(node):
        """Generate an xpath that would return node."""
        path = []
        node = node
        while node.parent:
            count = 0
            for sibling in node.parent.children:
                if sibling == node: break
                if sibling.tag == node.tag: count += 1
            else: assert False # somehow node is not a child of its parent???
            path.insert(0, "/{}[{}]".format(node.tag, count))
            node = node.parent
        assert node.root # having no parent should mean node is the root
        path.insert(0, "/{}".format(node.tag))
        return "".join(path)
    
    @staticmethod
    def xpath(root, path):
        """Return the node within root that matches path."""
        tags = path.split("/")[1:]
        tag = tags.pop(0)
        if root.tag != tag:
            raise ValueError(
                "tag {} of path {} does not match root tag {} in file {}"
                .format(tag, path, root.tag, root.url))
        node = root
        for tag in tags:
            tag, num = tag.split("[")
            num = int(num[:-1])
            count = 0
            for child in node.children:
                if tag == child.tag:
                    if count == num: break
                    count += 1
            else: raise ValueError(
                "tag count /{}[{}] of path {} not found in file {}"
                .format(tag, num, path, root.url))
            node = child
        return node

    def interpolate(self, n0, n1, t):
        """Compare the trees with indices n0 and n1, interpolating at time t.

        n0, n1 are integers, indices for self.trees
        t is a float between 0 and 1, inclusive
        t=0 is initial, returns self.trees[n0]
        t=1 is final,   returns self.trees[n1]

        Here's a list, per tag, as to what "interpolate" means.
            path: linearly interpolates between points
        Anything else just takes the state of the tree at n0.
        """
        #TODO: find or create a deep copy command for trees
        out_tree = self.trees[n0]
        tree0 = self.trees[n0]
        tree1 = self.trees[n1]
        biject0 = self.bijects[n0]
        biject1 = self.bijects[n1]
        for key in sorted(biject0):

            i0 = biject0[key]
            i1 = biject1[key]
            out_node = out_tree.children[i0]
            node0 = tree0.children[i0]
            node1 = tree1.children[i1]
            
            ### now ready to interpolate between node0 and node1

            if node0.tag == "path":
                data0 = self.path_str_to_data(node0['d'])
                data1 = self.path_str_to_data(node1['d'])

                out_data = []
                for cmd0, cmd1 in zip(data0, data1):
                    #TODO: write support for relative (lowercase) commands
                    out_cmd = [cmd0[0]]
                    for i in range(1, len(cmd0)):
                        out_num = (1-t)*cmd0[i] + t*cmd1[i]
                        out_cmd.append(out_num)
                    out_data.append(tuple(out_cmd))
                out_node['d'] = self.path_data_to_str(out_data)

        return out_tree

    @staticmethod
    def tree_to_clip(tree):
        png = 'tmp.png'
        surface = cairosvg.surface.PNGSurface(tree, png, 96)
        surface.finish()
        imageclip = mpy.ImageClip(png, duration=1)
        return imageclip.img

    def make_frame(self, t):
        i, r = divmod(t, 1)
        i = int(i)
        tree = self.interpolate(i, i+1, r)
        fg = self.tree_to_clip(tree)
        bg = mpy.ColorClip((2560, 1440), (.5, .5, .5), duration=1)
        return mpy.CompositeVideoClip([bg, fg]).make_frame(0)

def main():
    filenames = sorted(glob.glob('plaininkhand*.svg'))
    trans = Transition(filenames)
    clip = mpy.VideoClip(trans.make_frame, duration=len(filenames)-1)
    clip.write_videofile("test.avi", codec="png", fps=10)

if __name__ == "__main__":
    main()
