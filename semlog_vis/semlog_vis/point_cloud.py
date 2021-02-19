from PIL import Image
import numpy as np
import time


class PointCloudGenerator():
    """Class for generate point cloud from RGB and depth image pair."""

    def depthConversion(self, PointDepth):
        """Adjust the relative depth in UE4."""

        f = self.focal_length
        H = self.height
        W = self.width
        i_c = np.float(H) / 2 - 1
        j_c = np.float(W) / 2 - 1
        columns, rows = np.meshgrid(np.linspace(
            0, W - 1, num=W), np.linspace(0, H - 1, num=H))
        DistanceFromCenter = ((rows - i_c)**2 + (columns - j_c)**2)**(0.5)
        PlaneDepth = PointDepth / (1 + (DistanceFromCenter / f)**2)**(0.5)
        return PlaneDepth

    def __init__(self, rgb_file, depth_file, focal_length, scalingfactor):
        self.rgb_file = rgb_file
        self.depth_file = depth_file
        self.focal_length = focal_length
        self.scalingfactor = scalingfactor
        self.rgb = Image.open(rgb_file)
        self.width = self.rgb.size[0]
        self.height = self.rgb.size[1]
        self.depth = Image.open(depth_file).convert('I')
        self.depth = self.depthConversion(self.depth)
        
    def calculate(self,flag_depth_conversion=False):
        """Calculate the 3D position according to the depth data."""

        t1 = time.time()
        depth = np.asarray(self.depth).T
        self.Z = depth / self.scalingfactor
        X = np.zeros((self.width, self.height))
        Y = np.zeros((self.width, self.height))
        for i in range(self.width):
            X[i, :] = np.full(X.shape[1], i)

        self.X = ((X - self.width / 2) * self.Z) / self.focal_length
        for i in range(self.height):
            Y[:, i] = np.full(Y.shape[0], i)
        self.Y = ((Y - self.height / 2) * self.Z) / self.focal_length

        df = np.zeros((7, self.width * self.height))
        df[0] = self.X.T.reshape(-1)
        df[1] = -self.Y.T.reshape(-1)
        df[2] = -self.Z.T.reshape(-1)
        img = np.array(self.rgb)
        df[3] = img[:, :, 0:1].reshape(-1)
        df[4] = img[:, :, 1:2].reshape(-1)
        df[5] = img[:, :, 2:3].reshape(-1)
        self.df = df.astype(np.float16)
        t2 = time.time()
        print('calcualte 3d point cloud Done.', t2 - t1)

    def write_ply(self,path):
        """Save the point cloud as a .ply file."""
        t1 = time.time()
        head = '''ply
        format ascii 1.0
        element vertex %d
        property float x
        property float y
        property float z
        property uchar red
        property uchar green
        property uchar blue
        property uchar alpha
        end_header
        ''' % (self.width * self.height)
        # If focal_length is large, keep more decimal point as the x,y,z values
        # are very small.
        np.savetxt(path, self.df.T, fmt=[
                   '%3.5f', '%3.5f', '%3.5f', '%d', '%d', '%d', '%d'], header=head, comments='')

        t2 = time.time()
        print("Write into .ply file Done.", t2 - t1)

    # def show_point_cloud(self):
    #     """Show the point cloud directly with open3d."""
    #     pcd = read_point_cloud(self.pc_file)
    #     draw_geometries([pcd])

    def save_npy(self,path,alpha=False):
        """Save the .npy file of the point cloud."""
        data=self.df.copy()
        if alpha is False:
            data=data[:6]
        np.save(path,data)




