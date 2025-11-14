package com.happy.travian.dto;

public class CreateServerRequest {
  private String code;
  private String region;
  private String speed;
  private String startDate;
  public String getCode() { return code; }
  public void setCode(String code) { this.code = code; }
  public String getRegion() { return region; }
  public void setRegion(String region) { this.region = region; }
  public String getSpeed() { return speed; }
  public void setSpeed(String speed) { this.speed = speed; }
  public String getStartDate() { return startDate; }
  public void setStartDate(String startDate) { this.startDate = startDate; }
}