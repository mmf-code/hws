cmake_minimum_required(VERSION 3.5)
project(cpr_office_gazebo)

find_package(ament_cmake REQUIRED)

# Install mesh files (3D models and textures)
install(DIRECTORY meshes/
  DESTINATION share/${PROJECT_NAME}/meshes
)

# Install URDF files
install(DIRECTORY urdf/
  DESTINATION share/${PROJECT_NAME}/urdf
)

ament_package()
