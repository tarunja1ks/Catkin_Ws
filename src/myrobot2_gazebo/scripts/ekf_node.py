import rospy
from std_msgs.msg import String, Float64, Float64MultiArray
import numpy as np
from geometry_msgs.msg import Pose2D,PoseStamped
from sensor_msgs.msg import PointCloud2

class EKF:
    def __init__(self):
       rospy.init_node('listener',anonymous=True) #anonymous true technically not needed
    
       #initializing a subcriber onto the wheel velocities and then onto the steering angle
       rospy.Subscriber("/odom", Float64MultiArray, self.wheel_callback)
       rospy.Subscriber("/steering_angle", Float64, self.steering_callback)
       
       #initializing an orbslam d435 subscriber
       rospy.Subscriber("/orb_slam3/camera_pose", PoseStamped, self.camera_pose_callback)
       rospy.Subscriber("/orb_slam3/tracked_points",PointCloud2,self.orb_callback)
       
       #publishing robot pose
       self.pose_pub = rospy.Publisher('/ekf_pose', Pose2D, queue_size=1)
       
       #initializing the values for the velocities of the wheels and also the steering
       self.P=np.eye(4)
       self.Q=np.eye(4)*0.005
       self.wheel_velocities=np.array([0,0,0,0]) # rl, rr, fl, frr
       self.steering_angle=0
       self.curr_state=np.zeros([4])
       self.dt=0.05
       self.wheel_base = 0.2965
       self.wheel_radius = 0.050 
       
       self.timer = rospy.Timer(rospy.Duration(self.dt), self.predict_callback)
       
       # orb tracking check
       self.orb_tracking=False
       
    def predict_callback(self, event):
        self.predict()
        
    def orb_callback(self,msg):
        if(msg.width>0):
            rospy.loginfo("Orbslam tracking is on")
            self.orb_tracking=True
        else:
            rospy.loginfo("ITS NOT ON")
            self.orb_tracking=False
        
       
    def wheel_callback(self,data):
        self.wheel_velocities=np.array(data.data)
        self.update_encoder()
        
    def steering_callback(self,data):
        self.steering_angle=data.data
        
    def camera_pose_callback(self, data):
        pass
        self.update_camera(data.x, data.y, data.theta)
        
    def predict(self):
        # updating position estimate using motion model
        v_linear = self.curr_state[3]
        # v_linear=(self.wheel_velocities[0]+self.wheel_velocities[1])/2
        theta=self.curr_state[2]
        self.curr_state[2]=np.arctan2(np.sin(self.curr_state[2]),np.cos(self.curr_state[2]))
        theta_mid=(theta+self.curr_state[2])/2 #calculating the midpoint of heading between movement timesteps
        self.curr_state[0]+=(v_linear*np.cos(theta_mid))*self.dt
        self.curr_state[1]+=(v_linear*np.sin(theta_mid))*self.dt
        
        # calculating the jacobians with state respect to state
        A=np.eye(4)
        A[0][2]=-v_linear*np.sin(theta_mid)*self.dt
        A[1][2]=v_linear*np.cos(theta_mid)*self.dt
        A[0, 3] = np.cos(theta_mid) * self.dt
        A[1, 3] = np.sin(theta_mid) * self.dt
        A[2, 3] = np.tan(self.steering_angle) / self.wheel_base * self.dt
        
        #calculating the uncertainity Covariance matrix
        self.P=np.linalg.multi_dot([A,self.P,A.T])+self.Q
        
        msg = Pose2D(x=self.curr_state[0], y=self.curr_state[1], theta=self.curr_state[2])
        self.pose_pub.publish(msg)
    
    def update_camera(self,x,y,theta):
        H=np.diag([1,1,1,0])[:3]
        R=np.diag([0.05**2,0.05**2,0.02**2])
        Z=np.array([x,y,theta])
        self.update(H,R,Z)
        msg = Pose2D(x=self.curr_state[0], y=self.curr_state[1], theta=self.curr_state[2])
        self.pose_pub.publish(msg)
        
    def update_encoder(self):
        v_linear=((self.wheel_velocities[0]+self.wheel_velocities[1])/2)*self.wheel_radius
        H=np.array([[0,0,0,1]])
        R=np.array([[0.05**2]])
        Z=np.array([v_linear])
        self.update(H,R,Z)
        msg = Pose2D(x=self.curr_state[0], y=self.curr_state[1], theta=self.curr_state[2])
        self.pose_pub.publish(msg)
        
    def update(self,H,R,Z):
        # update stuff here
        # calculating the kalman gain, which is the scale for the innovation term
        K=np.linalg.multi_dot([self.P,H.T,np.linalg.inv(np.linalg.multi_dot([H,self.P,H.T])+R)])
        # finding the innovation term multiplied by the kalman gain and updating our state measurement
        self.curr_state=self.curr_state+K@(Z-H@self.curr_state)
        # scaling down the uncertainty Covariance
        self.P=(np.eye(4)-K@H)@self.P
             
              
       
       
if __name__ == "__main__": 
    Localizer=EKF()
    rospy.spin()
    
