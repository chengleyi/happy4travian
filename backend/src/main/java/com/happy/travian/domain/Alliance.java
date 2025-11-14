package com.happy.travian.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "alliances")
public class Alliance {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;
  @Column(name = "server_id", nullable = false)
  private Long serverId;
  @Column(name = "name", nullable = false, length = 64)
  private String name;
  @Column(name = "tag", nullable = false, length = 16)
  private String tag;
  @Column(name = "description")
  private String description;
  @Column(name = "created_by", nullable = false)
  private Long createdBy;
  public Long getId() { return id; }
  public void setId(Long id) { this.id = id; }
  public Long getServerId() { return serverId; }
  public void setServerId(Long serverId) { this.serverId = serverId; }
  public String getName() { return name; }
  public void setName(String name) { this.name = name; }
  public String getTag() { return tag; }
  public void setTag(String tag) { this.tag = tag; }
  public String getDescription() { return description; }
  public void setDescription(String description) { this.description = description; }
  public Long getCreatedBy() { return createdBy; }
  public void setCreatedBy(Long createdBy) { this.createdBy = createdBy; }
}