package com.happy.travian.domain;

import jakarta.persistence.*;
import java.time.LocalDate;

@Entity
@Table(name = "servers")
public class Server {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(name = "code", nullable = false, length = 32)
  private String code;

  @Column(name = "region", length = 32)
  private String region;

  @Column(name = "speed", length = 16)
  private String speed;

  @Column(name = "start_date")
  private LocalDate startDate;

  @Column(name = "status", length = 16)
  private String status;

  public Long getId() { return id; }
  public void setId(Long id) { this.id = id; }
  public String getCode() { return code; }
  public void setCode(String code) { this.code = code; }
  public String getRegion() { return region; }
  public void setRegion(String region) { this.region = region; }
  public String getSpeed() { return speed; }
  public void setSpeed(String speed) { this.speed = speed; }
  public LocalDate getStartDate() { return startDate; }
  public void setStartDate(LocalDate startDate) { this.startDate = startDate; }
  public String getStatus() { return status; }
  public void setStatus(String status) { this.status = status; }
}