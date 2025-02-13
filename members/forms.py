{% extends "base.html" %}

{% block title %}超級管理者後台{% endblock %}

{% block content %}
  <h1>超級管理者後台</h1>

  {% if message %}
    <div class="alert alert-info">{{ message }}</div>
  {% endif %}

  <h2>匯入每日銷售明細</h2>
  <form method="post" enctype="multipart/form-data">
      {% csrf_token %}
      {{ form.as_p }}
      <button type="submit" class="btn btn-primary">上傳並匯入</button>
  </form>

  <hr>

  <h2>會員資料管理</h2>
  <table class="table table-striped">
    <thead>
      <tr>
        <th>使用者名稱</th>
        <th>Email</th>
        <th>是否超級管理者</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      {% for member in members %}
      <tr>
        <td>{{ member.username }}</td>
        <td>{{ member.email }}</td>
        <td>{{ member.is_superuser }}</td>
        <td>
          <!-- 這裡示範連結到 Django 管理後台的使用者編輯頁面，您也可以自訂其他功能 -->
          <a href="{% url 'admin:auth_user_change' member.id %}" class="btn btn-sm btn-secondary">編輯</a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
<!-- ✅ 手動同步 Google Sheets 按鈕 -->
<form method="post">
    {% csrf_token %}
    <button type="submit" name="sync_google_sheets" class="btn btn-primary">🔄 手動同步 Google Sheets</button>
</form>

{% if message %}
<p>{{ message }}</p>
{% endif %}

<!-- ✅ 超級管理者登出按鈕 -->
<form method="post" action="{% url 'logout' %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-danger">🚪 登出</button>
</form>
<p>{{ message }}</p>

{% endblock %}
