package com.happy.travian.config;

import com.happy.travian.controller.GameAccountController;
import com.happy.travian.controller.TribeController;
import com.happy.travian.controller.VillageController;
import com.happy.travian.controller.TroopController;
import com.happy.travian.controller.ServerController;
import com.happy.travian.controller.HealthController;
import com.happy.travian.controller.DbController;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

@Configuration
public class MappingsLogger implements CommandLineRunner {
  private final RequestMappingHandlerMapping mapping;
  private final ApplicationContext ctx;

  public MappingsLogger(RequestMappingHandlerMapping mapping, ApplicationContext ctx) {
    this.mapping = mapping;
    this.ctx = ctx;
  }

  @Override
  public void run(String... args) {
    System.out.println("==> Registered request mappings");
    mapping.getHandlerMethods().forEach((info, method) -> {
      System.out.println(info);
    });
    System.out.println("==> Controller bean presence");
    System.out.println("HealthController: " + ctx.getBeansOfType(HealthController.class).size());
    System.out.println("DbController: " + ctx.getBeansOfType(DbController.class).size());
    System.out.println("ServerController: " + ctx.getBeansOfType(ServerController.class).size());
    System.out.println("TribeController: " + ctx.getBeansOfType(TribeController.class).size());
    System.out.println("GameAccountController: " + ctx.getBeansOfType(GameAccountController.class).size());
    System.out.println("VillageController: " + ctx.getBeansOfType(VillageController.class).size());
    System.out.println("TroopController: " + ctx.getBeansOfType(TroopController.class).size());
  }
}