#include <iostream>
#include <string>
#include "duco_driver/DucoCobot.h"

std::string ip = "192.168.1.110";

namespace DucoRPC
{
    class DucoCobot;
};

int main()
{
    DucoRPC::DucoCobot *duco_cobot = nullptr;
    duco_cobot = new DucoRPC::DucoCobot(ip, 7003);
    try
    {
        int result = duco_cobot->open();
        std::cout << "open: " << result << std::endl;
        result = duco_cobot->power_on(true);
        std::cout << "power_on: " << result << std::endl;
        result = duco_cobot->enable(true);
        std::cout << "enable: " << result << std::endl;

        std::vector<double> joints = {0, 0, 1.570796, 0, -1.570796, 0};
        result = duco_cobot->movej2(joints, 1, 1, 0, true);
        std::cout << "joint: " << result << std::endl;

        std::cout << duco_cobot->get_version() << std::endl;
        duco_cobot->close();
    }
    catch (...)
    {
        std::cout << "main error!" << std::endl;
        duco_cobot->close();
    }
}