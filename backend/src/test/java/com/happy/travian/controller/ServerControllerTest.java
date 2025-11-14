package com.happy.travian.controller;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class ServerControllerTest {
  @Autowired
  private TestRestTemplate rest;

  @Test
  void createAndList() {
    var body = "{\"code\":\"t1\",\"region\":\"CN\",\"speed\":\"x1\",\"startDate\":\"2025-11-01\"}";
    var headers = new HttpHeaders();
    headers.setContentType(MediaType.APPLICATION_JSON);
    var resp = rest.postForEntity("/api/v1/servers", new HttpEntity<>(body, headers), String.class);
    assertEquals(HttpStatus.OK, resp.getStatusCode());
    var list = rest.getForEntity("/api/v1/servers", String.class);
    assertEquals(HttpStatus.OK, list.getStatusCode());
    assertTrue(list.getBody() != null && list.getBody().contains("t1"));
  }
}