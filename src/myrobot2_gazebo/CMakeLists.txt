cmake_minimum_required(VERSION 3.0.2)
project(myrobot2_gazebo)

find_package(catkin REQUIRED COMPONENTS
  gazebo_ros
  roscpp
  rospy
  ackermann_msgs
)

find_package(gazebo REQUIRED)

catkin_package()

include_directories(
  plugins
  ${catkin_INCLUDE_DIRS}
  ${GAZEBO_INCLUDE_DIRS}
)

link_directories(${GAZEBO_LIBRARY_DIRS})

add_compile_options(
  -std=c++14
  -Wno-deprecated
  -Wno-enum-constexpr-conversion
  -D_LIBCPP_ENABLE_CXX17_REMOVED_UNARY_BINARY_FUNCTION
)

add_library(mushr_ackermann_plugin SHARED
  plugins/mushr_ackermann_plugin.cpp
)

target_link_libraries(mushr_ackermann_plugin
  ${catkin_LIBRARIES}
  ${GAZEBO_LIBRARIES}
)