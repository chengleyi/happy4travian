package com.happy.travian.domain;

import jakarta.persistence.*;

@Entity
@Table(name = "users")
public class User {
  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;
  @Column(name = "nickname", nullable = false, length = 64)
  private String nickname;
  @Column(name = "wechat_openid", length = 64)
  private String wechatOpenid;
  public Long getId() { return id; }
  public void setId(Long id) { this.id = id; }
  public String getNickname() { return nickname; }
  public void setNickname(String nickname) { this.nickname = nickname; }
  public String getWechatOpenid() { return wechatOpenid; }
  public void setWechatOpenid(String wechatOpenid) { this.wechatOpenid = wechatOpenid; }
}